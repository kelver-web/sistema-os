from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import filters as drf_filters
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from accounts.permissions import IsAdmin, IsTechOrAdmin
from service_orders.models import ServiceOrder
from service_orders.api.serializers import ServiceOrderSerializer, ServiceOrderItemSerializer


class ServiceOrderViewSet(viewsets.ModelViewSet):
    queryset = ServiceOrder.objects.all()
    serializer_class = ServiceOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    # Filtros e Ordenação
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_fields = ["status", "technician", "client", "priority"]
    search_fields = ["reported_problem", "technical_fidings", "solution_description"]
    ordering_fields = ["priority", "opened_at", "deadline"]
    ordering = ["-priority", "opened_at"]

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAdmin()]

        return [
            permission() for permission in self.permission_classes
        ]  # abrir OS: qualquer papel

    def perform_create(self, serializer):
        serializer.save(opened_by=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsTechOrAdmin])
    def assumir(self, request, pk=None):
        # Assumir OS, pode ser feito por tecnico ou admin, mas nao por outro
        service_order = self.get_object()
        service_order.technician = request.user
        service_order.status = ServiceOrder.Status.IN_PROGRESS
        service_order.started_at = timezone.now()
        service_order.save()
        return Response(self.get_serializer(service_order).data)

    @action(detail=True, methods=["post"], permission_classes=[IsTechOrAdmin])
    def concluir(self, request, pk=None):
        service_order = self.get_object()
        service_order.status = ServiceOrder.Status.COMPLETED
        service_order.completed_at = timezone.now()
        service_order.save()
        return Response(self.get_serializer(service_order).data)
    
    @action(detail=True, methods=["post", "get"], url_path="items")
    def items(self, request, pk=None):
        service_order = self.get_object()
        
        if request.method == "POST":
            # Regra de negócio 7.1: itens só em OS Pendente ou Em Andamento
            if service_order.status not in [
                ServiceOrder.Status.PENDING,
                ServiceOrder.Status.IN_PROGRESS,
            ]:
            
                return Response(
                    {"detail": "Itens só podem ser adicionados em OS Pendente ou Em Andamento."},
                    status=400,
                )
            serializer = ServiceOrderItemSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(service_order=service_order)
            return Response(serializer.data, status=201)
        
        items = service_order.items.all()
        page = self.paginate_queryset(items)
        serializer = ServiceOrderItemSerializer(page or items, many=True)
        
        if page is not None:
            return self.get_paginated_response(serializer.data)
        
        return Response(serializer.data)
