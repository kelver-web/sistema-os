# ADR 001 — Timeline da OS: chamada explícita em vez de signal

**Status:** aceito
**Data:** Semana 09
**Card:** "A entidade de auditoria do fluxo (histórico de eventos da OS)"

## Contexto

`ServiceTimeLine` registra os eventos da OS: quem fez o quê, quando. O model já
existe. A dúvida é **quando** a linha é criada:

- **A)** automaticamente, via `post_save` no model
- **B)** explicitamente, no ponto do código que muda o status

Sem essa decisão, a timeline fica órfã: existe no banco e nunca é preenchida.
Esse era o estado real do projeto — o model estava lá desde o commit `409cdfd`
sem nenhuma escrita.

## Decisão

**Chamada explícita, centralizada em `service_orders/services.py`.**

A transição de status acontece em um único lugar — a action `transicionar` do
viewset — que chama `registrar_transicao()`. Essa função valida a transição
contra `can_transition`, salva a OS e cria a timeline, tudo dentro de
`transaction.atomic()`.

## Justificativa

### Por que não signal

**1. Esconde a escrita.** Com `post_save`, `service_order.save()` em qualquer
arquivo dispara criação de timeline. Quem lê o código não vê o efeito colateral.

**2. A garantia é falsa.** `post_save` **não** dispara em `QuerySet.update()` nem
em `bulk_update()`. O signal dá sensação de cobertura total e entrega metade.
Pior: o comportamento fica diferente dependendo de *como* o código salvou, o que
vira bug intermitente.

**3. Perde a intenção.** O signal observa que o status mudou, mas não sabe
*quem* mudou nem *por quê*. Um técnico assumindo a OS e um admin corrigindo um
status errado produzem o mesmo evento no signal. A distinção — que é justamente
o valor da auditoria — se perde ou tem que ser inferida do `request`, que o model
não conhece.

**4. Difícil de testar.** Signal exige gravar no banco. `can_transition`, que é a
decisão de verdade, roda como função pura: 70 testes em 0.07s, sem fixture, sem
`db`. Isolar a regra foi o que permitiu validar a matriz antes de tocar na API.

**5. Efeito fantasma.** Qualquer `update()` futuro — um script de correção de
dados, um management command, um import — grava eventos na timeline sem ninguém
pedir. Em auditoria, evento não-requestado é ruído que ninguém sabe explicar.

### Por que explícita

**1. Ponto único de mutação.** Só a action `transicionar` muda status. Isso
torna a regra "toda mudança de status gera timeline" verificável por leitura:
um `grep` por `status =` acha um lugar só.

**2. Atomicidade.** Status e timeline na mesma transação de banco. Se a
timeline falhar, o status não muda. Sem isso, uma OS pode mudar de status sem
registro nenhum — e o histórico mente.

**3. Registra a intenção.** `registrar_transicao` recebe o `usuario` e uma
`descricao`cto descrevendo o ato. "Técnico João assumiu a OS" é informação de
negócio; "status mudou" não é.

**4. Testável isoladamente.** O service recebe e devolve objetos, sem conhecer
HTTP. Testa-se a regra sem subir view.

**5. Sinais continuam disponíveis para o que é deles.** Invalidar cache, enviar
notificação, marcar métricas. Coisas que realmente devem acontecer sempre, sem
depender de disciplina do developer.

## Consequências

**Ruim:** a action `transicionar` vira o gargalo. Todo caminho que muda status
precisa passar por ela. Novas actions (`assumir`, `concluir`) existem por
compatibilidade e delegam para ela — mas o caminho canônico é `transicionar`.

**Ruim:** anotações manuais de estado (`started_at`, `completed_at`) rodam no
service. Se alguém criar uma OS já em `COMPLETED` direto no admin, os
timestamps ficam vazios. Aceito: admin é operação exceptional e supervisionada.

**Bom:** o teste de integração "toda mudança de status gera exatamente uma
timeline" é possível e significativo. Com signal seria tautologia.

**Bom:** dá pra escrever o teste que realmente importa — status inválido **não**
muda nada. Estado e auditoria rejeitados juntos.

## Alternativas descartadas

| Alternativa | Por que não |
|---|---|
| `post_save` no model | Garantia falsa (não cobre `update()`), esconde escrita, perde intenção |
| Service Layer completo com DI | Exagero agora. O service é um módulo de funções; DI entra na Semana 15 se a复杂度 justificar |
| Event sourcing (OS é uma sequência de eventos) | Modelo mental mais puro, mas reescreve o app inteiro. Fora de escopo |
| Deixar a timeline pra cada action escrever | Repete `ServiceTimeLine.objects.create` em 7 lugares. Divergem no primeiro esquecimento |

## Onde a regra vive

| Artefato | Papel |
|---|---|
| `service_orders/transitions.py` | Quais transições são legais (puro, sem Django) |
| `service_orders/services.py` | Executa a transição: valida, salva, audita, atomicamente |
| `service_orders/api/viewsets.py` | Expõe a action HTTP e bloqueia `PATCH` com status |
| `docs/diagrama-estados.md` | Diagrama e tabela de permissões, derivados da matriz |
