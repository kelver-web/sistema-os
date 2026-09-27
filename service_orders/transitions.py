"""
Regras de transição de status da Ordem de Serviço.

Módulo puro: não importa Django, não toca no banco, não conhece Request.
Só recebe valores e devolve valores. Por isso roda no shell em milissegundos
e dá pra testar sem subir servidor nem criar fixture.

A matriz TRANSITIONS é a fonte única de verdade. Regra de ouro:
transição ausente da matriz é PROIBIDA. O padrão é negar, não permitir.
"""

from typing import Final

# Papéis como strings literais, de propósito: manter este módulo livre de
# qualquer import do Django. test_transitions.pyvalida que estes literals
# continuam em sincronia com accounts.models.User.Role.
ADMIN: Final = "admin"
TECH: Final = "tech"
ATTENDANT: Final = "attendant"

ALL_ROLES: Final = frozenset({ADMIN, TECH, ATTENDANT})

# Matriz de transições: origem -> destino -> papéis autorizados.
#
# PENDING .............. abre e fica parado
# AWAITING_PARTS ....... travada esperando peça no estoque
# IN_PROGRESS .......... técnico trabalhando
# AWAITING_APPROVAL .... serviço pronto, cliente não aprovou o valor
# COMPLETED ............ aprovado e finalizado
# DELIVERED ............ equipamento saiu da loja (terminal)
# CANCELED ............ desistência (terminal)
TRANSITIONS: Final[dict[str, dict[str, frozenset[str]]]] = {
    "PENDING": {
        # Peça necessária já identificada na recepção, sem precisar assumir.
        "AWAITING_PARTS": frozenset({TECH, ADMIN}),
        # Técnico assumiu o serviço.
        "IN_PROGRESS": frozenset({TECH, ADMIN}),
        # Cliente desistiu antes de começar.
        "CANCELED": ALL_ROLES,
    },
    "AWAITING_PARTS": {
        # Peça chegou, trabalho retoma.
        "IN_PROGRESS": frozenset({TECH, ADMIN}),
        # Cliente desistiu de esperar a peça.
        "CANCELED": ALL_ROLES,
    },
    "IN_PROGRESS": {
        # Descobriu que precisa de outra peça no meio do reparo.
        "AWAITING_PARTS": frozenset({TECH, ADMIN}),
        # Serviço pronto, enviado para aprovação do cliente.
        "AWAITING_APPROVAL": frozenset({TECH, ADMIN}),
        # Conserto simples com orçamento já acordado no balcão.
        "COMPLETED": frozenset({TECH, ADMIN}),
        "CANCELED": ALL_ROLES,
    },
    "AWAITING_APPROVAL": {
        # Cliente aprovou mas pediu mais trabalho, ou houve renegociação.
        "IN_PROGRESS": frozenset({TECH, ADMIN}),
        # Aprovação registrada no balcão. Técnico não auto-aprova preço.
        "COMPLETED": frozenset({ATTENDANT, ADMIN}),
        # Cliente recusou o valor.
        "CANCELED": ALL_ROLES,
    },
    "COMPLETED": {
        # Cliente retirou o equipamento.
        "DELIVERED": frozenset({ATTENDANT, ADMIN}),
        # Desfazer OS já concluída é excepcional: só admins.
        "CANCELED": frozenset({ADMIN}),
    },
    "DELIVERED": {},
    "CANCELED": {},
}


def can_transition(current_status: str, target_status: str, role: str) -> bool:
    """
    Diz se `role` pode mover uma OS de `current_status` para `target_status`.

    Parametros sao os valores brutos dos TextChoices de
    service_orders.models.ServiceOrder.Status e accounts.models.User.Role.

    Retorna False para status desconhecidos, para transições ausentes da
    matriz e para papéis não autorizados.
    """
    allowed_roles = TRANSITIONS.get(current_status, {}).get(target_status)
    if allowed_roles is None:
        return False
    return role in allowed_roles
