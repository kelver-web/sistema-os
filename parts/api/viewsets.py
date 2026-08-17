from rest_framework import viewsets
from parts.models import Part, PartMovement
from parts.api.serializers import PartSerializer, PartMovementSerializer
from accounts.permissions import IsAdmin, IsTechOrAdmin


class PartViewSet(viewsets.ModelViewSet):
    queryset = Part.objects.all()
    serializer_class = PartSerializer

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAdmin()]

        return [IsTechOrAdmin()]


class PartMovementViewSet(viewsets.ModelViewSet):
    queryset = PartMovement.objects.all()
    serializer_class = PartMovementSerializer
    permission_classes = [IsTechOrAdmin]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)