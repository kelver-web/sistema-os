import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from clients.models import Client


User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(username='testuser', password='testpass')

@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client

@pytest.mark.django_db
class TestClientViewset:
    def test_post_cria_client_e_seta_created_by_automaticamente(self, api_client, user):
        payload = {
            'name': 'Test Client',
            'email': 'client@teste.com',
            'phone': '1234567890',
        }
        response = api_client.post('/api/clients/', payload)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['created_by'] == user.id
        
    def test_post_ignora_created_by_forjado_no_payload(self, api_client, user):
        outro_user = User.objects.create_user(username='outrouser', password='testpass')
        payload = {
            'name': 'Test Client',
            'email': 'client@teste.com',
            'phone': '1234567890',
            'created_by': outro_user.id  # Tentativa de forjar o created_by
        }
        response = api_client.post('/api/clients/', payload)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['created_by'] == user.id  # Não é o outru usuário, mas sim o usuário autenticado
        
    def test_get_lista_clients(self, api_client, user):
        Client.objects.create(name='A', email='a@x', phone='84996969658', created_by=user)
        Client.objects.create(name='C', email='c@x', phone='84996969659', created_by=user)
        
        response = api_client.get('/api/clients/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert len(response.data['results']) == 2
        
    def test_delete_remove_client(self, api_client, user):
        client = Client.objects.create(name='ToDelete', email='a@x.com', phone='84996969658', created_by=user)
        response = api_client.delete(f'/api/clients/{client.id}/')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Client.objects.filter(id=client.id).exists()
        
    def test_requisicao_sem_autenticacao_e_bloqueada(self):
        client = APIClient() # Cliente sem autenticação
        response = client.get('/api/clients/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_requisicao_com_autenticacao_e_permissao(self, api_client):
        response = api_client.get('/api/clients/')
        assert response.status_code == status.HTTP_200_OK
        
        
        