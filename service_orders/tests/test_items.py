import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from clients.models import Client
from equipments.models import Equipment
from service_orders.models import ServiceOrder, ServiceOrderItem

User = get_user_model()


@pytest.fixture
def tech_user(db):
    return User.objects.create_user(
        username="tech_items", email="tech_items@teste.com",
        password="senha123", role=User.Role.TECH,
    )
    
@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="admin_items", email="admin_items@teste.com",
        password="senha123", role=User.Role.ADMIN, is_staff=True
    )
    
@pytest.fixture
def base_client_obj(admin_user):
    return Client.objects.create(
        name="Cliente Base",
        email="cliente_base_esc@teste.com",
        phone="84999990000",
        created_by=admin_user,
    )
    
@pytest.fixture
def base_equipment(base_client_obj):
    return Equipment.objects.create(
        client=base_client_obj, category="informatica",
        brand="Dell", model="X", condition="ok", serial_number="ITEMS-001",
    )
    
@pytest.fixture
def tech_client(tech_user):
    api = APIClient()
    api.force_authenticate(user=tech_user)
    return api

@pytest.fixture
def service_order(tech_client, base_client_obj, base_equipment):
    resp = tech_client.post(
        "/api/service-orders/",
        {
            "client": base_client_obj.id,
            "equipment": base_equipment.id,
            "reported_problem": "Problema de rede",
        },
    )
    return ServiceOrder.objects.get(id=resp.data["id"])


@pytest.mark.django_db
class TestServiceOrderItems:

    def test_criar_item_calcula_total_automaticamente(self, tech_client, service_order):
        resp = tech_client.post(f"/api/service-orders/{service_order.id}/items/", {
            "description": "Troca de fonte", "quantity": 2, "unit_price": "40.00",
        })

        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["total"] == "80.00"

    def test_listar_itens_da_os(self, tech_client, service_order):
        ServiceOrderItem.objects.create(
            service_order=service_order, description="Item A", quantity=1, unit_price=10,
        )
        ServiceOrderItem.objects.create(
            service_order=service_order, description="Item B", quantity=1, unit_price=20,
        )

        resp = tech_client.get(f"/api/service-orders/{service_order.id}/items/")

        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 2

    def test_service_order_nao_pode_ser_forjado_no_payload(self, tech_client, service_order):
        outra_os = ServiceOrder.objects.create(
            client=service_order.client, equipment=service_order.equipment,
            opened_by=service_order.opened_by, reported_problem="Outra OS",
        )

        resp = tech_client.post(f"/api/service-orders/{service_order.id}/items/", {
            "description": "Item", "quantity": 1, "unit_price": "10.00",
            "service_order": outra_os.id,  # tentativa de forjar
        })

        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["service_order"] == service_order.id  # não é outra_os.id

    def test_nao_permite_item_em_os_concluida(self, tech_client, service_order):
        tech_client.post(f"/api/service-orders/{service_order.id}/assumir/")
        tech_client.post(f"/api/service-orders/{service_order.id}/concluir/")

        resp = tech_client.post(f"/api/service-orders/{service_order.id}/items/", {
            "description": "Item tardio", "quantity": 1, "unit_price": "10.00",
        })

        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "Pendente ou Em Andamento" in resp.data["detail"]

    def test_permite_item_em_os_em_andamento(self, tech_client, service_order):
        tech_client.post(f"/api/service-orders/{service_order.id}/assumir/")

        resp = tech_client.post(f"/api/service-orders/{service_order.id}/items/", {
            "description": "Item durante execução", "quantity": 1, "unit_price": "10.00",
        })

        assert resp.status_code == status.HTTP_201_CREATED
        