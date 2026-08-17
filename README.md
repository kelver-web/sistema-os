# Sistema de Ordens de Serviço - Backend

API REST para gestão de ordens de serviço de assistência técnica, desenvolvida com Django REST Framework. Suporta três papéis de usuário (administrador, técnico e atendente), cada um com permissões específicas sobre os recursos do sistema.

## Funcionalidades

- **Autenticação JWT** (`accounts`) — Registro, login, refresh de token, verificação de token, dados do usuário logado
- **Controle de acesso por papel** — Permissões customizadas (admin, técnico, atendente) aplicadas em todos os recursos
- **Clientes** (`clients`) — CRUD de clientes, com validação de CPF/CNPJ
- **Equipamentos** (`equipments`) — Controle de equipamentos vinculados a clientes
- **Ordens de Serviço** (`service_orders`) — Abertura, atribuição de técnico, fluxo de status (pendente → em andamento → concluído), itens de serviço
- **Peças** (`parts`) — Gestão de estoque de peças e movimentações (entrada/uso)
- **Documentação interativa** — Swagger UI gerado automaticamente via `drf-spectacular`

## Tecnologias

- **Python** 3.13
- **Django** 6.0+
- **Django REST Framework** 3.17+
- **djangorestframework-simplejwt** (autenticação JWT)
- **drf-spectacular** (documentação OpenAPI/Swagger)
- **validate-docbr** (validação de CPF/CNPJ)
- **pytest** + **pytest-django** + **pytest-cov** (testes e cobertura)
- **PostgreSQL** (produção) / **SQLite** (desenvolvimento)
- **uv** (gerenciador de pacotes)

## Pré-requisitos

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL (para produção)

## Instalação

1. Clone o repositório:

```bash
git clone <url-do-repositorio>
cd sistem-backend-os
```

2. Instale as dependências:

```bash
uv sync
```

3. Execute as migrações:

```bash
uv run python manage.py migrate
```

4. Crie um superusuário:

```bash
uv run python manage.py createsuperuser
```

5. Inicie o servidor de desenvolvimento:

```bash
uv run python manage.py runserver
```

O servidor estará disponível em `http://127.0.0.1:8000/`.

## Autenticação e papéis

O sistema usa JWT (`djangorestframework-simplejwt`). Após o login, envie o token no header:

```
Authorization: Bearer <access_token>
```

| Endpoint | Método | Descrição |
|---|---|---|
| `/api/auth/register/` | POST | Registrar novo usuário |
| `/api/auth/login/` | POST | Login, retorna `access` + `refresh` |
| `/api/auth/refresh/` | POST | Renovar `access` token |
| `/api/auth/verify/` | POST | Verificar validade de um token |
| `/api/auth/me/` | GET | Dados do usuário autenticado |

Existem três papéis (`role`): **admin**, **tech** e **attendant**, cada um com permissões distintas sobre os recursos (ver seção de documentação da API).

## Documentação da API

Com o servidor rodando, a documentação interativa (Swagger) está disponível em:

```
http://127.0.0.1:8000/api/docs/
```

O schema OpenAPI bruto fica em `http://127.0.0.1:8000/api/schema/`.

## Testes

O projeto usa `pytest` com `pytest-django` e `pytest-cov`.

```bash
# Rodar toda a suíte
uv run pytest

# Rodar um arquivo específico
uv run pytest service_orders/tests/test_items.py -v

# Gerar relatório de cobertura navegável no navegador
uv run pytest --cov-report=html
xdg-open htmlcov/index.html
```

A cobertura de testes e o relatório detalhado (`term-missing`) já rodam automaticamente em toda execução de `pytest`, configurados via `pyproject.toml`.

## Comandos úteis

| Comando | Descrição |
|---|---|
| `uv run python manage.py runserver` | Iniciar servidor de desenvolvimento |
| `uv run python manage.py migrate` | Aplicar migrações do banco |
| `uv run python manage.py makemigrations` | Gerar novas migrações |
| `uv run python manage.py createsuperuser` | Criar superusuário |
| `uv run pytest` | Rodar suíte de testes com cobertura |
| `uv run pytest --cov-report=html` | Gerar relatório de cobertura em HTML |
| `uv run ruff check .` | Lint com ruff |
| `uv run ruff format .` | Formatar código com ruff |

## Estrutura do projeto

```
sistem-backend-os/
├── config/                # Configurações do Django
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/               # Autenticação, usuários, permissões por papel
│   ├── api/
│   ├── tests/
│   └── permissions.py
├── clients/                # Clientes
│   ├── api/
│   └── tests/
├── equipments/              # Equipamentos
│   ├── api/
│   └── tests/
├── service_orders/          # Ordens de serviço e itens
│   ├── api/
│   └── tests/
├── parts/                   # Peças e movimentações de estoque
│   ├── api/
│   └── tests/
├── manage.py
└── pyproject.toml
```

## Licença

Projeto aberto.