from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from clients.api.serializers import ClientSerializer
from clients.models import Client

from equipments.api.serializers import EquipmentSerializer
from accounts.permissions import IsAdmin


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    # Esta action permite obter equipamentos relacionados a um cliente específico.
    @action(detail=True, methods=['get'], url_path='equipments')
    def equipments(self, request, pk=None):
        client = self.get_object()
        equipment_qs = client.equipment.all()
        page = self.paginate_queryset(equipment_qs)
        serializer = EquipmentSerializer(page or equipment_qs, many=True)
        
        if page is not None:
            return self.get_paginated_response(serializer.data)
        
        return Response(serializer.data)
    
    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAdmin()]
        
        return [permissions.IsAuthenticated()]