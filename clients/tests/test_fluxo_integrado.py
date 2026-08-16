# clients/tests/test_fluxo_integrado.py
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
def test_fluxo_completo_client_equipment():
    user = User.objects.create_user(username="joao", password="senha123")
    api = APIClient()
    api.force_authenticate(user=user)

    # 1. Cria client
    resp = api.post(
        "/api/clients/",
        {
            "name": "Fluxo Teste",
            "email": "fluxo@teste.com",
            "phone": "84999998888",
            "document": "111.444.777-35",
        },
    )
    assert resp.status_code == status.HTTP_201_CREATED
    client_id = resp.data["id"]

    # 2. Cria equipment desse client
    resp = api.post(
        "/api/equipments/",
        {
            "client": client_id,
            "category": "informatica",
            "brand": "Dell",
            "model": "Inspiron 15",
            "serial_number": "FLX001",
            "condition": "Bom estado",
        },
    )
    assert resp.status_code == status.HTTP_201_CREATED
    equipment_id = resp.data["id"]

    # 3. Lista equipamentos do client (rota aninhada)
    resp = api.get(f"/api/clients/{client_id}/equipments/")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["count"] == 1

    # 4. Edita equipment
    resp = api.put(
        f"/api/equipments/{equipment_id}/",
        {
            "client": client_id,
            "category": "informatica",
            "brand": "Dell",
            "model": "Inspiron 15 (revisado)",
            "serial_number": "FLX001",
            "condition": "Revisado",
        },
    )
    assert resp.status_code == status.HTTP_200_OK

    # 5. Deleta equipment
    resp = api.delete(f"/api/equipments/{equipment_id}/")
    assert resp.status_code == status.HTTP_204_NO_CONTENT

    # 6. Confirma lista vazia
    resp = api.get(f"/api/clients/{client_id}/equipments/")
    assert resp.data["count"] == 0

    # 7. Deleta client (só funciona pq não há mais equipment vinculado — PROTECT)
    resp = api.delete(f"/api/clients/{client_id}/")
    assert resp.status_code == status.HTTP_204_NO_CONTENT

    # 8. Confirma client deletado
    resp = api.get(f"/api/clients/{client_id}/")
    assert resp.status_code == status.HTTP_404_NOT_FOUND

    # 9. Confirma equipment deletado
    resp = api.get(f"/api/equipments/{equipment_id}/")
    assert resp.status_code == status.HTTP_404_NOT_FOUND
