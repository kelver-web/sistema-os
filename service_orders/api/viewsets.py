from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from accounts.permissions import IsAdmin, IstTechOrAdmin
from service_orders.models import ServiceOrder
from service_orders.api.serializers import ServiceOrderSerializer


class ServiceOrderViewSet(viewsets.ModelViewSet):
    queryset = ServiceOrder.objects.all()
    serializer_class = ServiceOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAdmin()]

        return [permission() for permission in self.permission_classes] # abrir OS: qualquer papel
    
    def perform_create(self, serializer):
        serializer.save(opened_by=self.request.user)
        
        
    @action(detail=True, methods=['post'], permission_classes=[IstTechOrAdmin])
    def assumir(self, request, pk=None):
        service_order = self.get_object()
        service_order.technician = request.user
        service_order.status = ServiceOrder.Status.IN_PROGRESS
        service_order.started_at = timezone.now()
        service_order.save()
        return Response(self.get_serializer(service_order).data)
    
    @action(detail=True, methods=['post'], permission_classes=[IstTechOrAdmin])
    def concluir(self, request, pk=None):
        service_order = self.get_object()
        service_order.status = ServiceOrder.Status.COMPLETED
        service_order.completed_at = timezone.now()
        service_order.save()
        return Response(self.get_serializer(service_order).data)