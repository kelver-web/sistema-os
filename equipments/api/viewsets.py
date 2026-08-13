from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated

from equipments.api.serializers import EquipmentSerializer
from equipments.models import Equipment
from accounts.permissions import IsAdmin


class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAdmin()]

        return [permissions.IsAuthenticated()]
