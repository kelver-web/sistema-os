# Casos de borda da máquina de estados

Documento de pesquisa da Semana 09, sábado. Objetivo do card: reler o diagrama
de transições com espírito crítico e descobrir o que ele não cobre, **antes**
de escrever código.

A pergunta do card era: *e se a OS for cancelada no meio de "Aguardando Peça" e
já tem itens vinculados?*

Resposta curta: a transição está coberta. Tudo que vem depois dela, não.

---

## 1. A transição existe

```
AWAITING_PARTS -> CANCELED  =  {attendant, tech, admin}
```

`service_orders/transitions.py:45`. Qualquer papel cancela. A matriz está certa
nesse ponto, e por isso a pergunta passa: parece que o caso está tratado.

Não está. A matriz responde *"pode cancelar?"*. Ela não responde *"o que acontece
com o que já foi consumido?"*. São duas perguntas, e a segunda não tem dono hoje.

---

## 2. Onde a cadeia quebra

Três pontos, na ordem em que aparecem no caminho do problema.

### 2.1 O item da OS não sabe qual peça é

`ServiceOrderItem` tem exatamente estes campos:

```python
service_order, description, quantity, unit_price, total
```

`description` é `CharField` de texto livre. Não existe `ForeignKey` para `Part`.

Consequência: a linha do orçamento e o objeto físico do estoque não estão
ligados. O sistema sabe que a OS tem "Troca de placa-mãe, 1 un, R$ 400,00" e
sabe separadamente que a placa-mãe do modelo X foi consumida em outra OS. Não há
como casar as duas informações, nem manualmente com confiança.

Enquanto essa FK não existir, **é impossível** responder à pergunta do card de
forma satisfatória. Não é uma validação faltando; é um dado que não existe.

### 2.2 O movimento registra uso, mas não mexe no estoque

`PartMovementSerializer` é um `ModelSerializer` puro. Sem `create()`
customizado, sem `validate()`.

Criar um movimento `used`, quantidade 2, linked a uma OS:

| Efeito | Acontece? |
|---|---|
| Grava o registro no histórico | sim |
| Decrementa `Part.quantity` | **não** |
| Valida se existe estoque suficiente | **não** |

`Part.quantity` e a tabela de movimentações são **duas verdades desconectadas**.
Nada reconcilia as duas, e nada impede que fiquem discordando para sempre. Isso
não é um caso de borda do cancelamento: é um problema de consistência de estoque
que existe independently dele, e o cancelamento apenas torna visível.

### 2.3 Não há tipo de movimento capaz de expressar estorno

```python
class MovementType(models.TextChoices):
    IN   = "in",   "Entrada"
    USED = "used", "Usado"
```

Dois tipos. Entrada e consumo. O que existe para "a peça saiu do estoque
original, foi para a OS, e voltou porque a OS foi cancelada"? Nada.

E o caminho manual não resolve. Quem tentasse corrigir criando um `IN` perderia
a distinção entre **compra de fornecedor** e **estorno de OS cancelada** — são o
mesmo registro. Auditoria que não distingue devolução de compra não é auditoria.

---

## 3. O encadeamento completo

```
AWAITING_PARTS
  |
  | peça chega, técnico instala
  v
  PartMovement(USED, qtd=2)  --> ledger grava; estoque não baixa; não valida saldo
  |
  | status ainda AWAITING_PARTS
  v
  OS -> CANCELED              --> matrix permite (ALL_ROLES)
  |
  | nenhuma reversão ocorre
  v
  Peça fisicamente na bancada; sistema afirma que foi consumida.
  Se essa peça for vendida depois, nada registra a origem.
```

A janela do problema é o intervalo entre **registrar o consumo** e **mudar o
status para `IN_PROGRESS`**. A matriz trata `AWAITING_PARTS -> IN_PROGRESS`
como "peça chegou, trabalho retoma", mas nada obriga essas duas coisas a
acontecerem juntas. O técnico registra a peça, e a OS é cancelada antes de ele
mudar o status. Nesse instante, o estoque já não corresponde ao mundo.

---

## 4. Decisão

Três saídas foram consideradas.

| Opção | Comportamento no cancelamento | Problema |
|---|---|---|
| Estornar automático | Cria `RETURNED` e devolve ao estoque | Presume que a peça voltou intacta. Peça que esteve dentro de equipamento nem sempre volta, e devolver defeituosa ao estoque é pior que estoque errado |
| Cancelar e marcar | Cancela, peça vai para estado "retirada", decide depois | Adia a decisão e cria um estado novo para governar |
| **Bloquear com override** | Recusa para `tech`/`attendant`; `admin` pode, com registro na timeline | Exige intervenção humana no caso de estoque pendente |

**Adotada: bloquear com override de admin.**

Três razões.

**1. É a única que não inventa informação.** As outras duas assumem algo que o
sistema não sabe: que a peça voltou inteira, ou que alguém resolverá depois.
Bloquear recusa precisamente o que não pode ser respondido com o que se tem.

**2. Segue o princípio que o módulo já declara.** `transitions.py:9` — *"transição
ausente da matriz é PROIBIDA. O padrão é negar, não permitir."* O módulo já é
fail-closed. Uma exceção fail-open no cancelamento seria incoerente com o resto
do desenho.

**3. O override de admin não é novidade, é o padrão do arquivo.** `COMPLETED ->
CANCELED` já é exclusivo de `ADMIN` (linha 68), com o comentário *"Desfazer OS já
concluída é excepcional: só admins."*. Cancelar OS com estoque pendente é a
mesma situação: excepcional, e quem tem visão do negócio é o admin.

### A regra, escrita

> **Cancelar uma OS que tenha movimento `USED` pendente é recusado para `tech` e
> `attendant`. `admin` pode cancelar, e a timeline registra o cancelamento com
> essa marcação.**

O admin não é um atalho: é o ponto onde a decisão consciente acontece, e a
timeline existe para que essa decisão fique auditável.

---

## 5. Outros casos de borda encontrados na mesma leitura

O card pedia pelo menos um. A releitura achou cinco. Os dois primeiros merecem
decisão; os três últimos são para o card de implementação.

### 5.1 Técnico pode fechar OS sem passar por aprovação

`IN_PROGRESS -> COMPLETED` aceita `tech`. `AWAITING_APPROVAL -> COMPLETED`
aceita só `attendant`/`admin`.

Ou seja: a restrição "técnico não aprova preço próprio" existe, mas o técnico
pode contorná-la indo direto de `IN_PROGRESS` para `COMPLETED` — e nesse
caminho ele controla os itens, porque item só entra em `PENDING` e
`IN_PROGRESS`.

Isto é **proposital** e está correto para o negócio: conserto simples com preço
combinado no balcão não deve exigir aprovação. Mas a consequência precisa estar
escrita: **enquanto `IN_PROGRESS -> COMPLETED` existir para `tech`, a proteção
de preço é contornável por design.** Se a loja um dia exigir aprovação sempre,
esta transição muda — e a mudança é de regra de negócio, não de bug.

### 5.2 `AWAITING_APPROVAL` é um beco sem trava de feedback

`AWAITING_APPROVAL -> IN_PROGRESS` existe para o caso "cliente pediu mais
trabalho". Não há limite de quantas vezes esse ciclo pode correr. Não é bug —
nenhuma loja quer um contador artificial de idas e vindas — mas vale registrar
que o estado é potencialmente infinito por construção.

### 5.3 Cancelar OS concluída não trata restituição

`COMPLETED -> CANCELED` é exclusivo de `ADMIN`, correto. Mas se a OS já tinha
itens lançados e valor cobrado, cancelar não dispara restituição. O motivo do
cancelamento passa a ser obrigatório (decisão da sexta, regra 6 da seção 7.3),
o que cobre o registro. O dinheiro fica por conta do fluxo financeiro, fora do
escopo do módulo de estado.

### 5.4 `ServiceOrderItem` continua existindo após o cancelamento

Nada apaga itens de OS cancelada. Para auditoria isso está correto — o histórico
financeiro da tentativa precisa ser preservado. Mas a OS cancelada continua com
`total` calculado, e qualquer relatório que some OS por status vai somar valores
de trabalho que nunca foi cobrado. Filtro por `status != CANCELED` nos relatórios,
não exclusão.

### 5.5 Entrega sem custo e itens zerados

A regra 5 da seção 7.3 (OS sem cobrança efetiva não pode ser entregue) verifica
`final_cost` ou, se nulo, a soma dos itens. Uma OS com itens de valor zero passa
pela regra, porque a soma é zero e a regra só barra zero quando **não** há itens
declarados. Os dois casos precisam ser distinguidos no `service`: "sem itens" e
"itens de valor zero" são situações diferentes, e a regra atual as trata igual.

---

## 6. O que o card de implementação vai precisar

Não é um card só. São três, em ordem.

**A. Consistência de estoque** — o mais grave, e independente do cancelamento.
`PartMovement` deve alterar `Part.quantity` dentro de `transaction.atomic()` na
criação, e validar saldo antes. Sem isso, o campo `quantity` é decorativo e
qualquer relatório de estoque está errado hoje.

**B. Tipo de estorno** — `MovementType.RETURNED`, com a mesma
`ForeignKey` para `service_order` de origem, para que a devolução continue
auditável como devolução.

**C. FK de item para peça** — `ServiceOrderItem.part` nullable. Nullable porque
a OS pode ter linha de serviço que não é peça ("troca de pasta térmica", "limpeza
interna"). Preenchida quando for peça, deixa a ligação explícita.

**D. A regra do cancelamento** — só faz sentido depois de A e B. Bloquear sem
registrar estoque não funciona; registrar estoque sem tipo de estorno deixa o
ledger inconsistente. Por isso é a última, apesar de ser a que o card de sábado
descobriu primeiro.

### Fora de escopo

Nenhuma dessas mudanças altera a matriz de transições. `transitions.py` continua
com as mesmas 14 transições e os mesmos papéis. A regra do cancelamento mora no
service, não na matriz — porque depende de dados de estoque, e a matriz só sabe
status e papel.
