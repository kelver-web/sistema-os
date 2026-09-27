# Mapeamento das regras de negócio — seção 7.3

**Card:** Fechar a pesquisa antes de partir pra implementação (sexta, Semana 09)
**Escopo:** Onde cada regra da seção 7.3 do Notion vai ser implementada.
**Data:** Semana 09

Este documento é pesquisa. Não muda código. Serve de contrato para a
implementação da Semana 10 em diante.

---

## 1. Princípio de decisão

Cada regra mora na camada que responde à pergunta que ela precisa proteger.
A pergunta que decide o lugar:

> Se alguém escrever direto no banco, pelo admin do Django, ou por um script de
> correção, a regra ainda vale?
>
> Se **sim**, é constraint de banco. Se **não**, é service.

| Camada | Pergunta que responde | Como falha quando falta |
|---|---|---|
| Constraint no model | Isso é verdade no banco, venha de onde vier | Integridade depende de todo mundo lembrar de escrever a regra |
| Validator no serializer | O payload tem a forma correta | `500` em vez de `400`; lixo entra no banco |
| Permission | Quem pode fazer | Escalonamento de privilégio, vazamento de dado |
| Service | A operação faz sentido no estado atual | Regra de negócio furada em silêncio |
| ViewSet | Traduzir HTTP | Regra de negócio escrita dentro de `if` de view |

**Consequência prática:** regra que mora em serializer desaparece quando o dado
entra por outro caminho. Regra que mora em model nunca desaparece. Regra que
depende de estado (status, soma de itens) não pode morar em nenhum dos dois
primeiros — é service.

---

## 2. As quatro decisões

### 2.1 Serial number: único **global**, não por cliente

**O código hoje:** `UniqueConstraint(fields=["client", "serial_number"])`
**O Notion diz:** "único no sistema"

**Decisão: único global.** `UniqueConstraint(fields=["serial_number"])`.

**Raciocínio.** Número de série é identificador do fabricante e é global por
natureza — o mesmo número não aparece em dois fabricantes nem em duas unidades
do mesmo modelo. Duplicata significa o mesmo equipamento físico registrado
duas vezes, e aí o histórico do serviço se fragmenta entre duas linhas: a OS
antiga fica no primeiro cadastro, a nova no segundo, e nenhum relatório mostra
a história completa.

Aurea de "por cliente" faria sentido se o serial fosse etiqueta interna da
loja. Se a loja precisar de etiqueta própria, isso é **outro campo**
(`internal_tag`), não o mesmo campo com regra diferente.

Consequência: **o Notion está errado** e a seção 7.3 precisa ser corrigida pra
"número de série único no sistema".

Atenção na migração: se já existem dois clientes com o mesmo serial, a
constraint falha. Rodar um `SELECT serial_number, COUNT(*) ... HAVING
COUNT(*) > 1` antes e resolver as duplicatas.

Campo é `blank=True, null=True`, e o `save()` já converte vazio em `None`. Em
SQL, múltiplos `NULL` não colidem entre si, então equipamentos sem serial
continuam podendo ser vários. A constraint só bites onde há valor real.

### 2.2 "OS concluída sem custo não pode ser entregue"

**Decisão: a barreira fica na transição para `DELIVERED`, e o que se verifica
é a cobrança efetiva.**

```python
def cobrar_efetivo(ordem):
    """O que essa OS efetivamente cobra."""
    if ordem.final_cost is not None:
        return ordem.final_cost
    return sum((item.total for item in ordem.items.all()), Decimal("0"))
```

**Por que a barreira é na entrega, não na conclusão.** A regra original diz
"não pode ser **entregue**". Isso está certo e é uma escolha deliberada: a
conclusão é o fim do trabalho técnico, e o técnico precisa conseguir fechar o
serviço enquanto o financeiro ainda calcula o valor. Bloquear na conclusão
amarraria as duas equipes. A entrega é o último portão antes de o cliente
levar o equipamento embora — é ali que o dinheiro escapa se a regra falhar.

**Por que "cobrança efetiva" e não só `final_cost`.** Se a regra checasse só
`final_cost is None`, haveria um buraco: o técnico lança os itens (peça + mão de
obra, soma 180), mas esquece de preencher `final_cost`. A OS tem preço
calculado e `final_cost` vazio. Checando só o campo, a entrega passaria e a
loja teria worked o serviço sem lançamento. A soma dos itens é o segundo sinal,
e cobre esse caso.

**Se a cobrança efetiva for zero, a entrega é bloqueada com 400.**

**Exceção: serviço gratuito.** Garantia, cortesia,viladão. Não criar flag
`cost_waived` agora — é complexidade que ninguém pediu. O caminho é o admin
lançar o valor do serviço mesmo sendo cortesia, ou registrar o motivo na
descrição da transição, que já vai para a timeline. Se o volume de gratuitas
crescer e isso virar operação, a flag entra na Semana 11 junto com o controle
de estoque.

### 2.3 Motivo de cancelamento: campo novo no model

**Decisão: campo `cancellation_reason` no `ServiceOrder`, preenchido pelo
service, exigido na transição para `CANCELED`.**

```python
cancellation_reason = models.TextField("Motivo do cancelamento", blank=True)
```

**Por que campo novo e não reusar um campo livre.** `ServiceOrder` não tem
campo de notas livres — tem `reported_problem`, `technical_findings` e
`solution_description`, todos com semântica técnica específica. Não há o que
reusar. E reusar um deles seria errado: "solução" de uma OS cancelada não
existe.

**Por que no model e não só na timeline.** São dois padrões de acesso
diferentes. A tela de detalhe da OS quer mostrar "Cancelada — cliente desistiu"
sem percorrer a timeline, e um relatório de "por que cancelamos" quer filtrar
por motivo direto. Ambos são fáceis com coluna,(mapped by join.

**Por que preenchido pelo service e não pelo serializer.** O motivo pertence ao
*evento de cancelamento*, não ao estado corrente da OS. Se o serializer aceitasse
`cancellation_reason` como campo comum, o cliente da API poderia escrever o
motivo numa OS ativa, e o campo ficaria inconsistente com o status. O service
escreve, o serializer valida formato.

**O motivo vai nas duas places.** No model para consulta e exibição, e na
`description` da timeline para o rastro de auditoria ficar completo.

### 2.4 Preço de venda abaixo do custo: não bloqueia, avisa

**Decisão: valores negativos são bloqueados. `sale_price < supplier_price` gera
aviso, não bloqueio.**

**Negativos: bloqueado em duas camadas.**
- `MinValueValidator(0)` no serializer, que dá a mensagem de `400` útil
- `CheckConstraint` no model, que garante a integridade

Isso é sobre o dado ser absurdo, não sobre política comercial. Não existe
cenário legítimo em que o preço de uma peça seja `-50`. Both layers because the
model constraint holds even when a script writes directly, and the serializer
validator gives the API consumer a message that says what's wrong.

**`sale_price < supplier_price`: só aviso.** Todo o mundo já?vendeu abaixo do
custo em promoção, liquidação, garantia de fabricante, cliente com contrato.
Bloquear no cadastro trava operação legítima e empurra o profissional a
cadastrar preço errado pra conseguir salvar, que é pior: o banco passa a
mentir em vez de recusar a operação.

Então: o serializer expõe `margin` e `has_negative_margin` como campos
somente-leitura, calculados a partir de `supplier_price` e `sale_price`. O
frontend exibe alerta visual. Quem decide é o humano, com o dado na tela.

Campos que ganham `MinValueValidator(0)`:

| Model | Campo |
|---|---|
| `ServiceOrder` | `estimated_cost`, `final_cost` |
| `ServiceOrderItem` | `unit_price` |
| `Part` | `supplier_price`, `sale_price` |
| `PartMovement` | `unit_price` |

`quantity` não entra na lista: já é `PositiveIntegerField`, o tipo garante.

---

## 3. Mapeamento completo

| # | Regra | Camada | Artefato | Estado |
|---|---|---|---|---|
| 1 | Número de série único | Constraint no model | `UniqueConstraint(["serial_number"])` | ⚠️ hoje é por cliente — corrigir |
| 2 | CPF/CNPJ com dígitos verificadores | Validator no serializer | `clients/validators.py` | ✅ feito |
| 3 | Email do cliente único | `unique=True` no model + `UniqueValidator` no serializer | `clients/models.py`, `clients/api/serializers.py` | ✅ feito nos dois níveis |
| 4a | Valores não negativos | `MinValueValidator` no serializer **e** `CheckConstraint` no model | 6 campos listados em 2.4 | ❌ não implementado |
| 4b | Venda abaixo do custo | Campo calculado somente-leitura + aviso no front | `PartSerializer.margin` | ❌ não implementado |
| 5 | OS sem custo não pode ser entregue | **Service** | `registrar_transicao` | ❌ não implementado |
| 6 | Cancelamento exige motivo | Campo no model + exigência no **service** | `ServiceOrder.cancellation_reason` | ❌ não implementado |
| 7 | Só admin deleta | Permission | `IsAdmin` em `get_permissions` dos 4 viewsets | ✅ feito |
| 8 | Itens só em Pendente/Em Andamento | **Service** | hoje no `if` do POST no viewset | ⚠️ funciona, lugar errado |

**Placar: 4 feitas, 2 no lugar errado, 4 não implementadas.**

---

## 4. O que muda, por camada

### 4.1 Model (`models.py` + migration)

```python
# equipments/models.py — de unique-por-cliente para unique global
constraints = [
    models.UniqueConstraint(
        fields=["serial_number"],
        name="unique_serial_number",
    )
]

# service_orders/models.py — novo campo
cancellation_reason = models.TextField("Motivo do cancelamento", blank=True)

# service_orders/models.py — CHECK de não negativo
constraints = [
    models.CheckConstraint(
        condition=Q(estimated_cost__gte=0) | Q(estimated_cost__isnull=True),
        name="estimated_cost_nao_negativo",
    ),
    models.CheckConstraint(
        condition=Q(final_cost__gte=0) | Q(final_cost__isnull=True),
        name="final_cost_nao_negativo",
    ),
]

# service_orders/models.py — CHECK nos itens
# parts/models.py — CHECK nos preços da peça e da movimentação
```

Antes da migration, rodar o `SELECT ... HAVING COUNT(*) > 1` para garantir que
não há serial repetido — se houver, a migration quebra.

### 4.2 Serializer

```python
# service_orders/api/serializers.py
estimated_cost = serializers.DecimalField(
    max_digits=10, decimal_places=2,
    required=False, allow_null=True, min_value=0,
)
final_cost = serializers.DecimalField(
    max_digits=10, decimal_places=2,
    required=False, allow_null=True, min_value=0,
)
```

```python
# parts/api/serializers.py
margin = serializers.SerializerMethodField()
has_negative_margin = serializers.SerializerMethodField()
```

### 4.3 Service

```python
# service_orders/services.py

REGRA_SEM_CUSTO = (
    "OS sem valor não pode ser entregue. "
    "Informe final_cost ou adicione itens antes de concluir a entrega."
)


@transaction.atomic
def registrar_transicao(ordem, status_desejado, usuario, descricao=None, motivo=None):
    if status_desejado == ServiceOrder.Status.DELIVERED and cobrar_efetivo(ordem) == 0:
        raise RegraDeNegocio(REGRA_SEM_CUSTO)

    if status_desejado == ServiceOrder.Status.CANCELED and not motivo:
        raise RegraDeNegocio("Cancelamento exige motivo.")

    # ... resto, e no final:
    if status_desejado == ServiceOrder.Status.CANCELED:
        ordem.cancellation_reason = motivo
```

E mover a regra dos itens de `viewsets.py` para cá, num
`adicionar_item(ordem, dados, usuario)` que o service chama. A action fica
fina: valida formato, chama o service, devolve `400` na exceção.

`RegraDeNegocio` é exceção nova, irmã de `TransicaoInvalida`, para a API
traduzir em `400` com mensagem. Uma classe só, com mensagem — o Week 15 Ex 1
pede `Result object` em vez de exceção, e essa é a hora de trocar as duas.

### 4.4 ViewSet

Só o necessário: trocar o `if` dos itens por uma chamada ao service, e
traduzir `RegraDeNegocio` em `400`. Nenhuma regra de negócio nova aqui.

---

## 5. Itens que ficam pra depois, com razão

| Item | Por que não agora |
|---|---|
| Flag `cost_waived` para serviço gratuito | Ninguém pediu. Se gratuita virar operação comum, entra na Semana 11 |
| Bloquear venda abaixo do custo | Trava promoção e garantia legítimas. O aviso no front resolve |
| Estorno de estoque em OS cancelada | É a Semana 11 (Ex 3: adicionar item → cancelar OS → estoque volta) |
| `internal_tag` separado do serial | Só se a loja usar etiqueta própria. Não é o caso agora |

---

## 6. Pendência que não é deste card

`accounts/urls.py:21` registra `auth/register/`, contradizendo a decisão de
que auto-cadastro não faz sentido para sistema interno. Aberta desde o commit
anterior. Precisa ser resolvida em um dos dois sentidos antes da Semana 12,
porque a Semana 14 testa fluxo de login e não deve ter duas rotas de entrada.
