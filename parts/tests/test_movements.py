import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from parts.models import Part, PartMovement

User = get_user_model()


@pytest.fixture
def tech_user(db):
    return User.objects.create_user(
        username="tech_mov", email="tech_mov@teste.com",
        password="senha123", role=User.Role.TECH,
    )


@pytest.fixture
def attendant_user(db):
    return User.objects.create_user(
        username="attendant_mov", email="attendant_mov@teste.com",
        password="senha123", role=User.Role.ATTENDANT,
    )


@pytest.fixture
def base_part(db):
    return Part.objects.create(
        name="Fonte ATX Teste", supplier_price="50.00", sale_price="80.00", quantity=10,
    )


@pytest.fixture
def tech_client(tech_user):
    api = APIClient()
    api.force_authenticate(user=tech_user)
    return api


@pytest.fixture
def attendant_client(attendant_user):
    api = APIClient()
    api.force_authenticate(user=attendant_user)
    return api


@pytest.mark.django_db
class TestPartMovements:

    def test_tech_cria_movimento_com_sucesso(self, tech_client, tech_user, base_part):
        resp = tech_client.post("/api/parts/movements/", {
            "part": base_part.id, "movement_type": "used",
            "quantity": 1, "unit_price": "80.00",
        })

        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["created_by"] == tech_user.id

    def test_attendant_nao_pode_criar_movimento(self, attendant_client, base_part):
        resp = attendant_client.post("/api/parts/movements/", {
            "part": base_part.id, "movement_type": "used",
            "quantity": 1, "unit_price": "80.00",
        })

        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_created_by_nao_pode_ser_forjado(self, tech_client, tech_user, base_part):
        outro_user = User.objects.create_user(
            username="outro_mov", password="senha123", role=User.Role.TECH,
        )
        resp = tech_client.post("/api/parts/movements/", {
            "part": base_part.id, "movement_type": "used",
            "quantity": 1, "unit_price": "80.00",
            "created_by": outro_user.id,  # tentativa de forjar
        })

        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["created_by"] == tech_user.id

    def test_listar_movimentos(self, tech_client, tech_user, base_part):
        PartMovement.objects.create(
            part=base_part, movement_type="in", quantity=5,
            unit_price=50, created_by=tech_user,
        )

        resp = tech_client.get("/api/parts/movements/")

        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 1