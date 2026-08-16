import pytest
from unittest.mock import Mock
from django.contrib.auth import get_user_model

from accounts.permissions import IsAdmin, IstTechOrAdmin


User = get_user_model()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="admin_user",
        email="admin_user@teste",
        password="testpass",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def tech_user(db):
    return User.objects.create_user(
        username="tech_user",
        email="tech_user@teste",
        password="testpass",
        role=User.Role.TECH,
    )


@pytest.fixture
def attendant_user(db):
    return User.objects.create_user(
        username="attendant_user",
        email="attendant_user@teste",
        password="testpass",
        role=User.Role.ATTENDANT,
    )


def make_request(user):
    """Cria um objeto request 'falso' o suficiente pra testar has_permission."""
    request = Mock()
    request.user = user
    return request


@pytest.mark.django_db
class TestIsAdmin:
    def test_admin_tem_permissao(self, admin_user):
        permission = IsAdmin()

        assert permission.has_permission(make_request(admin_user), None) is True

    def test_tech_nao_tem_permissao(self, tech_user):
        permission = IsAdmin()

        assert permission.has_permission(make_request(tech_user), None) is False

    def test_attendant_nao_tem_permissao(self, attendant_user):
        permission = IsAdmin()

        assert permission.has_permission(make_request(attendant_user), None) is False

    def test_usuario_nao_autenticado_nao_tem_permissao(self):
        request = make_request(Mock(is_authenticated=False))
        permission = IsAdmin()

        assert permission.has_permission(request, None) is False


@pytest.mark.django_db
class TestIsTechOrAdmin:
    def test_admin_tem_permissao(self, admin_user):
        permission = IstTechOrAdmin()

        assert permission.has_permission(make_request(admin_user), None) is True

    def test_tech_tem_permissao(self, tech_user):
        permission = IstTechOrAdmin()

        assert permission.has_permission(make_request(tech_user), None) is True

    def test_attendant_nao_tem_permissao(self, attendant_user):
        permission = IstTechOrAdmin()

        assert permission.has_permission(make_request(attendant_user), None) is False
