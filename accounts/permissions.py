from rest_framework.permissions import BasePermission

from accounts.models import User


class IsAdmin(BasePermission):
    """Permite acesso apenas a usuários com role 'admin'."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == User.Role.ADMIN
        )

class IstTechOrAdmin(BasePermission):
    """Permite acesso apenas a usuários com role=TECH ou role=ADMIN."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in [User.Role.TECH, User.Role.ADMIN]
        )
