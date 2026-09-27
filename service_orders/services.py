"""
Camada de serviço da Ordem de Serviço.

Funções que carregam regra de negócio e orquestram escrita no banco. Ficam
entre a camada HTTP (viewsets) e o model. Não conhecem Request nem Response:
recebem objetos e devolvem objetos ou levantam exceção de domínio.

Ver docs/adr-001-timeline.md para a decisão de a timeline ser criada aqui, por
chamada explícita, e não por signal.
"""

from django.db import transaction
from django.utils import timezone

from service_orders.models import ServiceOrder, ServiceTimeLine
from service_orders.transitions import can_transition

# Rótulos gravados em ServiceTimeLine.action. Constantes em vez de literais
# soltos para o histórico ser pesquisável e o teste poder garantir o contrato.
ACTION_TRANSICAO = "status_change"
ACTION_ATRIBUICAO = "technician_assigned"
ACTION_CRIACAO = "created"

# Status que preenchem qual campo de timestamp ao serem alcançados.
TIMESTAMP_POR_STATUS = {
    ServiceOrder.Status.IN_PROGRESS: "started_at",
    ServiceOrder.Status.COMPLETED: "completed_at",
    ServiceOrder.Status.DELIVERED: "delivered_at",
}


class TransicaoInvalida(Exception):
    """
    Transição recusada. Carrega dados suficientes para a API montar uma
    resposta útil em vez de um 400 genérico.
    """

    def __init__(self, status_atual, status_desejado, role):
        self.status_atual = status_atual
        self.status_desejado = status_desejado
        self.role = role
        super().__init__(str(self))

    def __str__(self):
        return (
            f"Transição não permitida: {self.status_atual} -> "
            f"{self.status_desejado} para o papel '{self.role}'."
        )


@transaction.atomic
def registrar_transicao(ordem, status_desejado, usuario, descricao=None):
    """
    Move a OS para `status_desejado` e registra o evento na timeline.

    A transition é validada contra a matriz de transições. Status e timeline
    são gravados na mesma transação de banco: ou os dois acontecem, ou nenhum.
    """
    status_atual = ordem.status

    if not can_transition(status_atual, status_desejado, usuario.role):
        raise TransicaoInvalida(status_atual, status_desejado, usuario.role)

    ordem.status = status_desejado

    campo_timestamp = TIMESTAMP_POR_STATUS.get(status_desejado)
    if campo_timestamp:
        setattr(ordem, campo_timestamp, timezone.now())

    ordem.save(
        update_fields=["status", campo_timestamp] if campo_timestamp else ["status"]
    )

    ServiceTimeLine.objects.create(
        service_order=ordem,
        user=usuario,
        action=ACTION_TRANSICAO,
        description=descricao or f"Status alterado para {status_desejado}",
    )

    return ordem


@transaction.atomic
def atribuir_tecnico(ordem, tecnico, usuario):
    """
    Atribui um técnico à OS e move para Em Andamento.

    Se a OS já estiver em Em Andamento, a atribuição é apenas registrada na
    timeline: trocar o responsável no meio do serviço é operação normal.
    """
    ordem.technician = tecnico

    if ordem.status == ServiceOrder.Status.PENDING:
        registrar_transicao(
            ordem,
            ServiceOrder.Status.IN_PROGRESS,
            usuario,
            descricao=f"OS assumida por {tecnico.get_full_name() or tecnico.username}",
        )
        ordem.technician = tecnico
        ordem.save(update_fields=["technician"])
    else:
        ordem.save(update_fields=["technician"])
        ServiceTimeLine.objects.create(
            service_order=ordem,
            user=usuario,
            action=ACTION_ATRIBUICAO,
            description=f"Técnico {tecnico.get_full_name() or tecnico.username} atribuído",
        )

    return ordem


@transaction.atomic
def registrar_criacao(ordem, usuario):
    """Registra a abertura da OS na timeline."""
    ServiceTimeLine.objects.create(
        service_order=ordem,
        user=usuario,
        action=ACTION_CRIACAO,
        description="OS criada",
    )
    return ordem
