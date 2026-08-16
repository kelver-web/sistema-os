import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from clients.models import Client
from equipments.models import Equipment


User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="joao", password="senha123")


@pytest.fixture
def client_obj(user):
    return Client.objects.create(
        name="Cliente Teste",
        email="teste@exemplo.com",
        phone="84999999999",
        created_by=user,
    )


@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestEquipmentViewset:
    def test_post_equipment_direto_cria_com_sucesso(self, api_client, client_obj):
        payload = {
            "client": client_obj.id,
            "category": "informatica",
            "brand": "Dell",
            "model": "Inspiron 15",
            "serial_number": "SN123456",
            "condition": "Bom estado",
        }
        response = api_client.post("/api/equipments/", payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["client"] == client_obj.id

    def test_post_equipment_serial_duplicado_falha(self, api_client, client_obj):
        Equipment.objects.create(
            client=client_obj,
            category="informatica",
            brand="Dell",
            model="Inspiron 15",
            serial_number="SN123456",
            condition="Bom estado",
        )
        payload = {
            "client": client_obj.id,
            "category": "informatica",
            "brand": "Dell",
            "model": "Inspiron 15",
            "serial_number": "SN123456",  # Serial number duplicado
            "condition": "Bom estado",
        }
        response = api_client.post("/api/equipments/", payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestClientEquipmentNestedRoute:
    def test_lista_equipment_apenas_do_cliente_especifico(self, api_client, user):
        client_a = Client.objects.create(
            name="Cliente A", email="a@x", phone="84996969658", created_by=user
        )
        client_b = Client.objects.create(
            name="Cliente B", email="b@x", phone="84996969659", created_by=user
        )
        Equipment.objects.create(
            client=client_a,
            category="informatica",
            brand="Dell",
            model="Inspiron 15",
            serial_number="SN123456",
            condition="Bom estado",
        )
        Equipment.objects.create(
            client=client_a,
            category="informatica",
            brand="HP",
            model="Pavilion",
            serial_number="SN654321",
            condition="Bom estado",
        )
        Equipment.objects.create(
            client=client_b,
            category="informatica",
            brand="Lenovo",
            model="ThinkPad",
            serial_number="SN111222",
            condition="Bom estado",
        )
        response = api_client.get(f"/api/clients/{client_a.id}/equipments/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        brands = [item["brand"] for item in response.data["results"]]
        assert "Dell" in brands and "HP" in brands
        assert "Azus" not in brands

    def test_rota_aninhada_sem_autenticacao_e_bloqueada(self, client_obj):
        client = APIClient()  # Cliente não autenticado
        response = client.get(f"/api/clients/{client_obj.id}/equipments/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
