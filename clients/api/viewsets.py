from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from clients.api.serializers import ClientSerializer
from clients.models import Client


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
