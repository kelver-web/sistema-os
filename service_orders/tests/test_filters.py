import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from clients.models import Client
from equipments.models import Equipment
from service_orders.models import ServiceOrder

User = get_user_model()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="admin_filtros", email="admin_filtros@teste.com",
        password="senha123", role=User.Role.ADMIN, is_staff=True,
    )


@pytest.fixture
def tech_user(db):
    return User.objects.create_user(
        username="tech_filtros", email="tech_filtros@teste.com",
        password="senha123", role=User.Role.TECH,
    )


@pytest.fixture
def attendant_user(db):
    return User.objects.create_user(
        username="attendant_filtros", email="attendant_filtros@teste.com",
        password="senha123", role=User.Role.ATTENDANT,
    )


@pytest.fixture
def base_client_obj(admin_user):
    return Client.objects.create(
        name="Cliente Filtros", email="cliente_filtros@teste.com",
        phone="84999990000", created_by=admin_user,
    )


@pytest.fixture
def base_equipment(base_client_obj):
    return Equipment.objects.create(
        client=base_client_obj, category="informatica",
        brand="Dell", model="X", condition="ok", serial_number="FLT-001",
    )


@pytest.fixture
def tech_client(tech_user):
    api = APIClient()
    api.force_authenticate(user=tech_user)
    return api


@pytest.fixture
def duas_os(attendant_user, tech_user, base_client_obj, base_equipment):
    os1 = ServiceOrder.objects.create(
        client=base_client_obj, equipment=base_equipment, opened_by=attendant_user,
        reported_problem="Tela quebrada", priority=ServiceOrder.Priority.URGENT,
    )
    os2 = ServiceOrder.objects.create(
        client=base_client_obj, equipment=base_equipment, opened_by=attendant_user,
        reported_problem="Não liga de jeito nenhum", priority=ServiceOrder.Priority.LOW,
        technician=tech_user,
    )
    return os1, os2


@pytest.mark.django_db
class TestServiceOrderFiltros:

    def test_filtro_por_status(self, tech_client, duas_os):
        resp = tech_client.get("/api/service-orders/?status=PENDING")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 2  # as duas nascem PENDING

    def test_filtro_por_technician(self, tech_client, tech_user, duas_os):
        resp = tech_client.get(f"/api/service-orders/?technician={tech_user.id}")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 1

    def test_filtro_por_client(self, tech_client, base_client_obj, duas_os):
        resp = tech_client.get(f"/api/service-orders/?client={base_client_obj.id}")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 2

    def test_filtro_por_priority(self, tech_client, duas_os):
        resp = tech_client.get("/api/service-orders/?priority=4")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 1

    def test_busca_geral(self, tech_client, duas_os):
        resp = tech_client.get("/api/service-orders/?search=quebrada")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 1

    def test_ordenacao_por_prioridade_decrescente(self, tech_client, duas_os):
        resp = tech_client.get("/api/service-orders/?ordering=-priority")
        assert resp.status_code == status.HTTP_200_OK
        prioridades = [item["priority"] for item in resp.data["results"]]
        assert prioridades == sorted(prioridades, reverse=True)
