# Documentação da API — Sistema de Ordens de Serviço

Documentação de referência de todos os endpoints implementados. Para explorar interativamente, use o Swagger em `/api/docs/` (servidor precisa estar rodando).

## Sumário

1. [Autenticação](#1-autenticação)
2. [Clientes](#2-clientes)
3. [Equipamentos](#3-equipamentos)
4. [Ordens de Serviço](#4-ordens-de-serviço)
5. [Itens da Ordem de Serviço](#5-itens-da-ordem-de-serviço)
6. [Peças](#6-peças)
7. [Movimentações de Peças](#7-movimentações-de-peças)
8. [Dashboard](#8-dashboard)
9. [Controle de acesso por papel](#9-controle-de-acesso-por-papel)

---

## Convenções gerais

- Todas as rotas (exceto `register`, `login`, `refresh`, `verify`) exigem autenticação via header:
  ```
  Authorization: Bearer <access_token>
  ```
- Listagens são paginadas, retornando o formato:
  ```json
  { "count": 10, "next": null, "previous": null, "results": [...] }
  ```
- Erros de validação retornam `400` com o nome do campo e a mensagem:
  ```json
  { "campo": ["mensagem de erro"] }
  ```
- `401` = não autenticado (token ausente/inválido/expirado). `403` = autenticado, mas sem permissão para a ação.

---

## 1. Autenticação

App: `accounts`

### `POST /api/auth/register/`
Registra um novo usuário.

**Body:**
```json
{
  "username": "joao",
  "email": "joao@empresa.com",
  "password": "SenhaForte123!",
  "password_confirm": "SenhaForte123!"
}
```

**Resposta `201`:**
```json
{ "id": 4, "username": "joao", "email": "joao@empresa.com" }
```
Senha nunca é retornada. `role` nasce como `tech` por padrão (alterável só por admin via `/api/users/`).

### `POST /api/auth/login/`
Autentica e retorna os tokens JWT.

**Body:** `{ "username": "joao", "password": "SenhaForte123!" }`

**Resposta `200`:**
```json
{ "refresh": "eyJhbGci...", "access": "eyJhbGci..." }
```

**`401`** se credenciais inválidas.

### `POST /api/auth/refresh/`
Gera um novo `access` token a partir do `refresh`.

**Body:** `{ "refresh": "eyJhbGci..." }`
**Resposta `200`:** `{ "access": "eyJhbGci..." }`

### `POST /api/auth/verify/`
Verifica se um token ainda é válido (sem consumir dados do usuário).

**Body:** `{ "token": "eyJhbGci..." }`
**Resposta:** `200` (vazio) se válido, `401` se inválido/expirado.

### `GET /api/auth/me/`
Retorna os dados do usuário autenticado.

**Resposta `200`:**
```json
{ "id": 4, "username": "joao", "email": "joao@empresa.com" }
```

---

## 2. Clientes

App: `clients` — Base: `/api/clients/`

| Método | Rota | Descrição | Quem pode |
|---|---|---|---|
| GET | `/api/clients/` | Listar clientes | qualquer autenticado |
| POST | `/api/clients/` | Criar cliente | qualquer autenticado |
| GET | `/api/clients/{id}/` | Detalhes | qualquer autenticado |
| PUT | `/api/clients/{id}/` | Atualizar | qualquer autenticado |
| DELETE | `/api/clients/{id}/` | Remover | **admin** |

### `POST /api/clients/`
**Body:**
```json
{
  "name": "João Silva",
  "email": "joao.silva@email.com",
  "phone": "84999998888",
  "document": "111.444.777-35",
  "address": "Rua das Flores, 123",
  "notes": "Cliente indicado"
}
```
`document` aceita CPF ou CNPJ (com ou sem pontuação) — validado com dígito verificador. Campo opcional.

**Resposta `201`:**
```json
{
  "id": 1, "name": "João Silva", "email": "joao.silva@email.com",
  "phone": "84999998888", "document": "111.444.777-35",
  "address": "Rua das Flores, 123", "notes": "Cliente indicado",
  "created_by": 4, "created_at": "2026-08-08T09:15:00-03:00",
  "updated_at": "2026-08-08T09:15:00-03:00"
}
```
`created_by` é preenchido automaticamente com o usuário autenticado — não pode ser enviado no payload.

**Erros comuns (`400`):**
- Email duplicado: `{"email": ["Já existe um cliente cadastrado com este e-mail."]}`
- Documento inválido: `{"document": ["CPF inválido. Verifique os dígitos informados."]}`

---

## 3. Equipamentos

App: `equipments` — Base: `/api/equipments/`

| Método | Rota | Descrição | Quem pode |
|---|---|---|---|
| GET | `/api/clients/{id}/equipments/` | Equipamentos de um cliente (rota aninhada) | qualquer autenticado |
| GET | `/api/equipments/` | Listar todos | qualquer autenticado |
| POST | `/api/equipments/` | Criar equipamento | qualquer autenticado |
| GET | `/api/equipments/{id}/` | Detalhes | qualquer autenticado |
| PUT | `/api/equipments/{id}/` | Atualizar | qualquer autenticado |
| DELETE | `/api/equipments/{id}/` | Remover | **admin** |

### `POST /api/equipments/`
**Body:**
```json
{
  "client": 1,
  "category": "informatica",
  "brand": "Dell",
  "model": "Inspiron 15",
  "serial_number": "SN123456",
  "accessories": "Carregador, mouse",
  "condition": "Bom estado"
}
```
`category` aceita: `informatica`, `eletronicos`, `telefonia`, `impressoras`, `eletrodomesticos`, `outros`. `serial_number` é opcional, mas único por cliente.

**Resposta `201`:**
```json
{
  "id": 5, "client": 1,
  "client_detail": { "id": 1, "name": "João Silva" },
  "category": "informatica", "brand": "Dell", "model": "Inspiron 15",
  "serial_number": "SN123456", "accessories": "Carregador, mouse",
  "condition": "Bom estado", "created_at": "2026-08-08T09:20:00-03:00"
}
```
`client_detail` traz nome do cliente (útil ao listar `/api/equipments/` sem filtro por cliente).

---

## 4. Ordens de Serviço

App: `service_orders` — Base: `/api/service-orders/`

| Método | Rota | Descrição | Quem pode |
|---|---|---|---|
| GET | `/api/service-orders/` | Listar (com filtros) | qualquer autenticado |
| POST | `/api/service-orders/` | Abrir OS | qualquer autenticado |
| GET | `/api/service-orders/{id}/` | Detalhes | qualquer autenticado |
| PUT | `/api/service-orders/{id}/` | Atualizar dados gerais | qualquer autenticado |
| DELETE | `/api/service-orders/{id}/` | Remover | **admin** |
| POST | `/api/service-orders/{id}/assumir/` | Assumir OS | **tech ou admin** |
| POST | `/api/service-orders/{id}/concluir/` | Concluir OS | **tech ou admin** |

### `POST /api/service-orders/`
**Body:**
```json
{
  "client": 1,
  "equipment": 5,
  "reported_problem": "Notebook não liga",
  "priority": 3
}
```
`priority`: `1` baixa, `2` média (default), `3` alta, `4` urgente.

**Resposta `201`:**
```json
{
  "id": 8, "client": 1, "equipment": 5, "opened_by": 4, "technician": null,
  "reported_problem": "Notebook não liga", "technical_fidings": "",
  "solution_description": "", "status": "PENDING", "priority": 3,
  "estimated_cost": null, "final_cost": null,
  "opened_at": "2026-08-18T10:00:00-03:00", "started_at": null,
  "completed_at": null, "delivered_at": null, "deadline": null
}
```
`opened_by`, `status`, `technician`, `started_at`, `completed_at`, `opened_at` nunca vêm do payload — são controlados pelo servidor/pelas actions abaixo.

### `POST /api/service-orders/{id}/assumir/`
Atribui o técnico autenticado à OS e muda status para `IN_PROGRESS`. Sem body.

**Resposta `200`:** OS atualizada, com `technician` e `started_at` preenchidos.
**`403`** se quem chama for `attendant`.

### `POST /api/service-orders/{id}/concluir/`
Muda status para `COMPLETED` e preenche `completed_at`. Sem body.

**`403`** se quem chama for `attendant`.

### Fluxo de status (seção 7.1 do doc de arquitetura)
```
PENDING → IN_PROGRESS → COMPLETED → AWAITING_APPROVAL → DELIVERED
              ↕
        AWAITING_PARTS
Qualquer status → CANCELED
```

### Filtros, busca e ordenação em `GET /api/service-orders/`

| Query param | Tipo | Exemplo |
|---|---|---|
| `?status=` | igualdade exata | `?status=PENDING` |
| `?technician=` | igualdade exata (id do usuário) | `?technician=3` |
| `?client=` | igualdade exata (id do cliente) | `?client=1` |
| `?priority=` | igualdade exata | `?priority=4` |
| `?search=` | busca textual em `reported_problem`, `technical_fidings`, `solution_description` | `?search=tela quebrada` |
| `?ordering=` | ordenação; prefixo `-` = decrescente | `?ordering=-priority` |

Sem `?ordering=`, o padrão é `-priority, opened_at` (mais urgente primeiro, mais antiga primeiro dentro da mesma prioridade).

---

## 5. Itens da Ordem de Serviço

Rota aninhada dentro de `service_orders`.

| Método | Rota | Descrição | Quem pode |
|---|---|---|---|
| GET | `/api/service-orders/{id}/items/` | Listar itens da OS | qualquer autenticado |
| POST | `/api/service-orders/{id}/items/` | Adicionar item | qualquer autenticado, **só se OS estiver Pendente ou Em Andamento** |

### `POST /api/service-orders/{id}/items/`
**Body:**
```json
{ "description": "Troca de fonte", "quantity": 1, "unit_price": "80.00" }
```

**Resposta `201`:**
```json
{ "id": 1, "service_order": 8, "description": "Troca de fonte", "quantity": 1, "unit_price": "80.00", "total": "80.00" }
```
`total` é calculado automaticamente (`quantity × unit_price`). `service_order` vem da URL, nunca do payload.

**`400`** se a OS não estiver `PENDING`/`IN_PROGRESS`:
```json
{ "detail": "Itens só podem ser adicionados em OS Pendente ou Em Andamento." }
```

---

## 6. Peças

App: `parts` — Base: `/api/parts/`

| Método | Rota | Descrição | Quem pode |
|---|---|---|---|
| GET | `/api/parts/` | Listar peças | **tech ou admin** |
| POST | `/api/parts/` | Cadastrar peça | **tech ou admin** |
| GET | `/api/parts/{id}/` | Detalhes | **tech ou admin** |
| PUT | `/api/parts/{id}/` | Atualizar | **tech ou admin** |
| DELETE | `/api/parts/{id}/` | Remover | **admin** |

### `POST /api/parts/`
**Body:**
```json
{
  "name": "Fonte ATX", "manufacturer": "Corsair", "supplier": "Fornecedor X",
  "supplier_price": "50.00", "sale_price": "80.00", "quantity": 10, "location": "Prateleira A3"
}
```

---

## 7. Movimentações de Peças

Base: `/api/parts/movements/`

| Método | Rota | Descrição | Quem pode |
|---|---|---|---|
| GET | `/api/parts/movements/` | Listar movimentações | **tech ou admin** |
| POST | `/api/parts/movements/` | Registrar movimentação | **tech ou admin** |

### `POST /api/parts/movements/`
**Body:**
```json
{
  "part": 3, "service_order": 8, "movement_type": "used",
  "quantity": 1, "unit_price": "80.00", "notes": "Usada na OS #8"
}
```
`movement_type`: `in` (entrada em estoque) ou `used` (uso em OS). `service_order` é opcional.

**Resposta `201`:**
```json
{
  "id": 1, "part": 3, "service_order": 8, "movement_type": "used",
  "quantity": 1, "unit_price": "80.00", "notes": "Usada na OS #8",
  "created_by": 4, "created_at": "2026-08-18T11:00:00-03:00"
}
```
`created_by` vem do usuário autenticado, nunca do payload.

---

## 8. Dashboard

Base: `/api/dashboard/` — acesso restrito a **admin**.

### `GET /api/dashboard/`
**Resposta `200`:**
```json
{
  "total_ordens_servico": 42,
  "por_status": { "PENDING": 10, "IN_PROGRESS": 5, "COMPLETED": 20, "DELIVERED": 7 },
  "ordens_atrasadas": 3
}
```
`ordens_atrasadas` conta OS com `deadline` no passado e status ainda `PENDING`/`IN_PROGRESS`.

### `GET /api/dashboard/revenue/`
**Query param opcional:** `?periodo=<dias>` (default: `30`)

**Resposta `200`:**
```json
{ "periodo_dias": 30, "faturamento_total": 1250.00 }
```
Soma `final_cost` de OS com status `DELIVERED` dentro do período informado.

---

## 9. Controle de acesso por papel

| Recurso | Admin | Técnico | Atendente |
|---|---|---|---|
| Gerenciar usuários (`/api/users/`) | ✅ | ❌ | ❌ |
| CRUD Clientes | ✅ | ✅ | ✅ |
| CRUD Equipamentos | ✅ | ✅ | ✅ |
| Abrir OS | ✅ | ✅ | ✅ |
| Assumir OS | ✅ | ✅ | ❌ |
| Concluir OS | ✅ | ✅ | ❌ |
| Adicionar item à OS | ✅ | ✅ | ✅ |
| Cadastrar peças / movimentações | ✅ | ✅ | ❌ |
| Ver relatórios/dashboard | ✅ | ❌ | ❌ |
| Excluir qualquer registro | ✅ | ❌ | ❌ |

`401` = não autenticado. `403` = autenticado, mas o papel não tem permissão para a ação.
