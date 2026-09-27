# service_orders/tests/test_transitions.py
"""
Testes da função pura de transição de status.

Nenhum destes testes precisa de banco: é o ganho de manter a regra de negócio
fora de view e serializer. Só o teste de sincronismo com o model toca o Django.
"""

import pytest
from accounts.models import User
from service_orders.models import ServiceOrder
from service_orders.transitions import (
    ADMIN,
    ALL_ROLES,
    ATTENDANT,
    TECH,
    TRANSITIONS,
    can_transition,
)

Status = ServiceOrder.Status

# Casos negatively confirmados: o par (origem, destino) é proibido para TODOS
# os papéis. Inclui exatamente o exemplo do card: Pendente -> Entregue direto.
FORBIDDEN_PAIRS = [
    # Nunca pular etapas do fluxo.
    (Status.PENDING, Status.COMPLETED),
    (Status.PENDING, Status.DELIVERED),
    (Status.PENDING, Status.AWAITING_APPROVAL),
    # Não voltar atrás.
    (Status.AWAITING_PARTS, Status.PENDING),
    (Status.IN_PROGRESS, Status.PENDING),
    (Status.AWAITING_APPROVAL, Status.PENDING),
    (Status.COMPLETED, Status.IN_PROGRESS),
    (Status.COMPLETED, Status.AWAITING_APPROVAL),
    # Estados terminais não têm saída nenhuma.
    (Status.DELIVERED, Status.IN_PROGRESS),
    (Status.DELIVERED, Status.CANCELED),
    (Status.CANCELED, Status.IN_PROGRESS),
    (Status.CANCELED, Status.PENDING),
    # Mudar para o mesmo status é no-op e poluiria a timeline.
    (Status.PENDING, Status.PENDING),
    (Status.COMPLETED, Status.COMPLETED),
]

# Pares (origem, destino, papel) que DEVEM ser permitidos.
ALLOWED_CASES = [
    (Status.PENDING, Status.IN_PROGRESS, TECH),
    (Status.PENDING, Status.IN_PROGRESS, ADMIN),
    (Status.PENDING, Status.AWAITING_PARTS, TECH),
    (Status.PENDING, Status.CANCELED, ATTENDANT),
    (Status.AWAITING_PARTS, Status.IN_PROGRESS, TECH),
    (Status.AWAITING_PARTS, Status.CANCELED, ATTENDANT),
    (Status.IN_PROGRESS, Status.AWAITING_PARTS, TECH),
    (Status.IN_PROGRESS, Status.AWAITING_APPROVAL, TECH),
    (Status.IN_PROGRESS, Status.COMPLETED, TECH),
    (Status.IN_PROGRESS, Status.CANCELED, ATTENDANT),
    (Status.AWAITING_APPROVAL, Status.IN_PROGRESS, TECH),
    (Status.AWAITING_APPROVAL, Status.COMPLETED, ATTENDANT),
    (Status.AWAITING_APPROVAL, Status.COMPLETED, ADMIN),
    (Status.COMPLETED, Status.DELIVERED, ATTENDANT),
    (Status.COMPLETED, Status.CANCELED, ADMIN),
]

# Pares (origem, destino, papel) que DEVEM ser negados por papel, mesmo que a
# transição exista na matriz para outro papel.
DENIED_BY_ROLE = [
    # Técnico não registra aprovação de preço: quem fala com o cliente é o balcão.
    (Status.AWAITING_APPROVAL, Status.COMPLETED, TECH),
    # Technician não entrega equipamento.
    (Status.COMPLETED, Status.DELIVERED, TECH),
    # Technician não desfaz OS concluída.
    (Status.COMPLETED, Status.CANCELED, TECH),
    # Atendente não mexe no ciclo técnico.
    (Status.PENDING, Status.IN_PROGRESS, ATTENDANT),
    (Status.IN_PROGRESS, Status.AWAITING_APPROVAL, ATTENDANT),
]


@pytest.mark.parametrize(("current", "target", "role"), ALLOWED_CASES)
def test_transicao_permitida(current, target, role):
    assert can_transition(current, target, role) is True


@pytest.mark.parametrize(("current", "target"), FORBIDDEN_PAIRS)
@pytest.mark.parametrize("role", sorted(ALL_ROLES))
def test_transicao_proibida(current, target, role):
    assert can_transition(current, target, role) is False


@pytest.mark.parametrize(("current", "target", "role"), DENIED_BY_ROLE)
def test_transicao_negada_por_papel(current, target, role):
    assert can_transition(current, target, role) is False


def test_pendente_para_entregue_e_negado():
    """Critério de pronto do card: Pendente -> Entregue direto é recusado."""
    for role in ALL_ROLES:
        assert can_transition(Status.PENDING, Status.DELIVERED, role) is False


@pytest.mark.parametrize(
    ("current", "target", "role"),
    [
        ("STATUS_QUE_NAO_EXISTE", Status.IN_PROGRESS, ADMIN),
        (Status.PENDING, "ALVO_QUE_NAO_EXISTE", ADMIN),
        ("STATUS_QUE_NAO_EXISTE", "ALVO_QUE_NAO_EXISTE", ADMIN),
    ],
)
def test_status_desconhecido_retorna_false_sem_levantar_excecao(current, target, role):
    assert can_transition(current, target, role) is False


def test_papel_desconhecido_e_negado():
    assert can_transition(Status.PENDING, Status.IN_PROGRESS, "superusuario") is False


def test_matriz_cobre_todos_os_status_do_model():
    """A matriz não pode deixar de fora nenhum status que existe no model."""
    status_do_model = {choice.value for choice in Status}
    status_na_matriz = set(TRANSITIONS)
    assert status_na_matriz == status_do_model


def test_matriz_nao_contem_papeis_inexistentes():
    papeis_do_model = {choice.value for choice in User.Role}
    papeis_na_matriz = set(ALL_ROLES)
    assert papeis_na_matriz == papeis_do_model


def test_toda_transicao_na_matriz_tem_pelo_menos_um_papel():
    for origem, destinos in TRANSITIONS.items():
        for destino, papeis in destinos.items():
            assert papeis, f"{origem} -> {destino} está na matriz sem papel nenhum"
