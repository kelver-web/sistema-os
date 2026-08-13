from rest_framework import viewsets
from accounts.models import User
from serializers import UserSerializer
from accounts.permissions import IsAdmin


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]