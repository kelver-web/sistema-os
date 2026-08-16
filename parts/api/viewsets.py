from rest_framework import viewsets
from parts.models import Part
from parts.api.serializers import PartSerializer
from accounts.permissions import IsAdmin, IstTechOrAdmin


class PartViewSet(viewsets.ModelViewSet):
    queryset = Part.objects.all()
    serializer_class = PartSerializer

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAdmin()]

        return [IstTechOrAdmin()]
