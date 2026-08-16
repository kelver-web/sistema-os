import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


@pytest.fixture
def api_client():
    client = APIClient()
    return client


@pytest.fixture
def existing_user(db):
    return User.objects.create_user(
        username="testuser", email="testuser@teste", password="testpass"
    )


@pytest.mark.django_db
class TestRegister:
    def test_registro_cria_usuario_com_sucesso(self, api_client):
        payload = {
            "username": "maria",
            "email": "maria@teste.com",
            "password": "SenhaForte123!",
            "password_confirm": "SenhaForte123!",
        }
        response = api_client.post("/api/auth/register/", payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert "password" not in response.data
        assert "password_confirm" not in response.data
        assert User.objects.filter(username="maria").exists()

    def test_registro_faz_hash_da_senha(self, api_client):
        payload = {
            "username": "maria",
            "email": "maria@teste.com",
            "password": "SenhaForte123!",
            "password_confirm": "SenhaForte123!",
        }
        api_client.post("/api/auth/register/", payload)

        user = User.objects.get(username="maria")
        assert user.password != "SenhaForte123!"
        assert user.check_password("SenhaForte123!")

    def test_registro_com_senhas_diferentes_falha(self, api_client):
        payload = {
            "username": "maria",
            "email": "maria@teste.com",
            "password": "SenhaForte123!",
            "password_confirm": "SenhaFraca123!",
        }
        response = api_client.post("/api/auth/register/", payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password_confirm" in response.data
        assert not User.objects.filter(username="maria").exists()

    def test_registro_com_senha_fraca_falha(self, api_client):
        payload = {
            "username": "maria",
            "email": "maria@teste",
            "password": "123",
            "password_confirm": "123",
        }
        response = api_client.post("/api/auth/register/", payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data


@pytest.mark.django_db
class TestLogin:
    def test_login_valido_retorna_tokens(self, api_client, existing_user):
        payload = {
            "username": "testuser",
            "password": "testpass",
        }
        response = api_client.post("/api/auth/login/", payload)

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_com_senha_errada_retorna_401(self, api_client, existing_user):
        payload = {
            "username": "testuser",
            "password": "wrongpass",
        }
        response = api_client.post("/api/auth/login/", payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_com_usuario_inexistente_retorna_401(self, api_client):
        payload = {
            "username": "nonexistentuser",
            "password": "testpass",
        }
        response = api_client.post("/api/auth/login/", payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestMeEndpoint:
    def test_me_sem_token_retorna_401(self, api_client):
        response = api_client.get("/api/auth/me/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_com_token_valido_retorna_dados_do_usuario(
        self, api_client, existing_user
    ):
        payload = {
            "username": "testuser",
            "password": "testpass",
        }
        login_response = api_client.post("/api/auth/login/", payload)
        access_token = login_response.data["access"]

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = api_client.get("/api/auth/me/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == "testuser"
        assert response.data["email"] == "testuser@teste"


@pytest.mark.django_db
class TestRefresh:
    def test_refresh_retorna_novo_access_token(self, api_client, existing_user):
        login_response = api_client.post(
            "/api/auth/login/", {"username": "testuser", "password": "testpass"}
        )
        refresh_token = login_response.data["refresh"]

        response = api_client.post("/api/auth/refresh/", {"refresh": refresh_token})

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_refresh_com_token_invalido_retorna_401(self, api_client):
        response = api_client.post("/api/auth/refresh/", {"refresh": "token-invalido"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
