from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from equipments.api.serializers import EquipmentSerializer
from equipments.models import Equipment


class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [IsAuthenticated]
