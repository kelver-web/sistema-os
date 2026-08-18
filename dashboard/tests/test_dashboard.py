import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="admin_dash", email="admin_dash@teste.com",
        password="senha123", role=User.Role.ADMIN, is_staff=True,
    )


@pytest.fixture
def tech_user(db):
    return User.objects.create_user(
        username="tech_dash", email="tech_dash@teste.com",
        password="senha123", role=User.Role.TECH,
    )


@pytest.fixture
def attendant_user(db):
    return User.objects.create_user(
        username="attendant_dash", email="attendant_dash@teste.com",
        password="senha123", role=User.Role.ATTENDANT,
    )


def client_para(user): # mock para simular request
    api = APIClient()
    api.force_authenticate(user=user)
    return api


@pytest.mark.django_db
class TestDashboard:

    def test_admin_acessa_dashboard(self, admin_user):
        resp = client_para(admin_user).get("/api/dashboard/")
        assert resp.status_code == status.HTTP_200_OK

    def test_tech_nao_acessa_dashboard(self, tech_user):
        resp = client_para(tech_user).get("/api/dashboard/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_attendant_nao_acessa_dashboard(self, attendant_user):
        resp = client_para(attendant_user).get("/api/dashboard/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_acessa_revenue(self, admin_user):
        resp = client_para(admin_user).get("/api/dashboard/revenue/")
        assert resp.status_code == status.HTTP_200_OK

    def test_tech_nao_acessa_revenue(self, tech_user):
        resp = client_para(tech_user).get("/api/dashboard/revenue/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN
