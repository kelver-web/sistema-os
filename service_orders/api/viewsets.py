from rest_framework import filters as drf_filters
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import IsAdmin, IsTechOrAdmin
from service_orders.models import ServiceOrder, ServiceOrderItem, ServiceTimeLine
from service_orders.services import (
    TransicaoInvalida,
    atribuir_tecnico,
    registrar_criacao,
    registrar_transicao,
)
from service_orders.api.serializers import (
    ServiceOrderItemSerializer,
    ServiceOrderSerializer,
    ServiceTimeLineSerializer,
)

# Status que aceitam item, conforme regra 7.1.
STATUS_ACEITAM_ITEM = [
    ServiceOrder.Status.PENDING,
    ServiceOrder.Status.IN_PROGRESS,
]


class ServiceOrderViewSet(viewsets.ModelViewSet):
    queryset = ServiceOrder.objects.select_related(
        "client", "technician", "opened_by", "equipment"
    ).prefetch_related("items")
    serializer_class = ServiceOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        drf_filters.SearchFilter,
        drf_filters.OrderingFilter,
    ]
    filterset_fields = ["status", "technician", "client", "priority"]
    search_fields = ["reported_problem", "technical_findings", "solution_description"]
    ordering_fields = ["priority", "opened_at", "deadline"]
    ordering = ["-priority", "opened_at"]

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAdmin()]
        return [permission() for permission in self.permission_classes]

    def perform_create(self, serializer):
        ordem = serializer.save(opened_by=self.request.user)
        registrar_criacao(ordem, self.request.user)

    def update(self, request, *args, **kwargs):
        """
        Bloqueia mudança de status via PATCH/PUT.

        O serializer já marca status como read_only, o que protege a criação.
        Mas num PATCH parcial o campo read_only é simplesmente ignorado em
        silêncio: o cliente manda status, recebe 200, e acredita que mudou.
        Validar aqui troca a surpresa por um 400 explícito.

        Status só muda pela action /transicionar/.
        """
        if "status" in request.data:
            return Response(
                {
                    "detail": (
                        "Status não pode ser alterado via PATCH ou PUT. "
                        "Use a action /transicionar/."
                    )
                },
                status=400,
            )
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=["post"], permission_classes=[IsTechOrAdmin])
    def assumir(self, request, pk=None):
        """Atalho para assumir a OS. Delega ao service."""
        ordem = self.get_object()
        atribuir_tecnico(ordem, request.user, request.user)
        return Response(self.get_serializer(self.get_queryset().get(pk=ordem.pk)).data)

    @action(detail=True, methods=["post"], permission_classes=[IsTechOrAdmin])
    def concluir(self, request, pk=None):
        """Atalho para concluir. Delega ao service."""
        ordem = self.get_object()
        try:
            registrar_transicao(
                ordem,
                ServiceOrder.Status.COMPLETED,
                request.user,
                descricao="Serviço concluído",
            )
        except TransicaoInvalida as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(self.get_serializer(self.get_queryset().get(pk=ordem.pk)).data)

    @action(detail=True, methods=["post"])
    def transicionar(self, request, pk=None):
        """
        Único caminho autorizado para mudar o status de uma OS.

        A validação, a gravação e a timeline acontecem em service_orders.services
        dentro de transaction.atomic(). Esta action só traduz HTTP para o service.
        """
        ordem = self.get_object()

        status_desejado = request.data.get("status")
        if not status_desejado:
            return Response({"detail": "Campo 'status' é obrigatório."}, status=400)

        validos = {choice.value for choice in ServiceOrder.Status}
        if status_desejado not in validos:
            return Response(
                {
                    "detail": f"Status inválido: '{status_desejado}'.",
                    "status_validos": sorted(validos),
                },
                status=400,
            )

        try:
            registrar_transicao(
                ordem,
                status_desejado,
                request.user,
                descricao=request.data.get("description"),
            )
        except TransicaoInvalida as exc:
            return Response(
                {
                    "detail": str(exc),
                    "status_atual": exc.status_atual,
                    "status_desejado": exc.status_desejado,
                },
                status=400,
            )

        return Response(self.get_serializer(self.get_queryset().get(pk=ordem.pk)).data)

    @action(detail=True, methods=["get"], url_path="timeline")
    def timeline(self, request, pk=None):
        """Histórico de eventos da OS, mais recente primeiro."""
        ordem = self.get_object()
        entries = ordem.timeline.all()
        page = self.paginate_queryset(entries)
        serializer = ServiceTimeLineSerializer(page or entries, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=True, methods=["post", "get"], url_path="items")
    def items(self, request, pk=None):
        ordem = self.get_object()

        if request.method == "POST":
            # Regra de negócio 7.1: itens só em OS Pendente ou Em Andamento
            if ordem.status not in STATUS_ACEITAM_ITEM:
                return Response(
                    {
                        "detail": "Itens só podem ser adicionados em OS Pendente ou Em Andamento."
                    },
                    status=400,
                )
            serializer = ServiceOrderItemSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(service_order=ordem)
            return Response(serializer.data, status=201)

        items = ordem.items.all()
        page = self.paginate_queryset(items)
        serializer = ServiceOrderItemSerializer(page or items, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


class ServiceOrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceOrderItemSerializer
    queryset = ServiceOrderItem.objects.all()

    def get_queryset(self):
        if self.kwargs.get("service_order_pk"):
            return ServiceOrderItem.objects.filter(
                service_order_id=self.kwargs["service_order_pk"]
            )
        return ServiceOrderItem.objects.all()

    def perform_create(self, serializer):
        if self.kwargs.get("service_order_pk"):
            serializer.save(service_order_id=self.kwargs["service_order_pk"])
        else:
            serializer.save()


class ServiceTimeLineViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ServiceTimeLineSerializer
    queryset = ServiceTimeLine.objects.all()
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset().select_related("user")
        if self.kwargs.get("service_order_pk"):
            return queryset.filter(service_order_id=self.kwargs["service_order_pk"])
        return queryset
