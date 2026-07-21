# Sistema de Ordens de Serviço - Backend

API REST para gestão de ordens de servico, desenvolvida com Django REST Framework.

## Funcionalidades

- **Ordens de Serviço** (`service_orders`) — Gerenciamento de ordens de trabalho/manutenção
- **Clientes** (`clients`) — Cadastro de clientes
- **Equipamentos** (`equipments`) — Controle de equipamentos dos clientes
- **Peças** (`parts`) — Gestão de peças e componentes
- **Usuários** (`accounts`) — Autenticação e gestão de usuários (técnicos, administradores)

## Tecnologias

- **Python** 3.13
- **Django** 6.0+
- **Django REST Framework** 3.17+
- **PostgreSQL** (produção) / **SQLite** (desenvolvimento)
- **JWT** (autenticação via `djangorestframework-simplejwt`)
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

## Comandos úteis

| Comando | Descrição |
|---------|-----------|
| `uv run python manage.py runserver` | Iniciar servidor de desenvolvimento |
| `uv run python manage.py migrate` | Aplicar migrações do banco |
| `uv run python manage.py makemigrations` | Gerar novas migrações |
| `uv run python manage.py createsuperuser` | Criar superusuário |
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
├── accounts/              # App de contas de usuários
├── clients/               # App de clientes
├── equipments/            # App de equipamentos
├── parts/                 # App de peças
├── service_orders/        # App de ordens de serviço
├── manage.py
└── pyproject.toml
```

## Licença

Projeto privado.
