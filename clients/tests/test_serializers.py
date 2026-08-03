import pytest
from django.contrib.auth import get_user_model
from clients.models import Client
from clients.api.serializers import ClientSerializer


User = get_user_model()


@pytest.mark.django_db
class TestClientSerializer:
    def setup_method(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpassword'
        )
        self.client_obj = Client.objects.create(
            name='Test Client',
            email='testclient@teste',
            phone='1234567890',
            created_by=self.user,
        )
        
    def test_client_serializer_sem_erros(self):
        serializer = ClientSerializer(self.client_obj)
        data = serializer.data
        
        assert data['name'] == 'Test Client'
        assert data['email'] == 'testclient@teste'
        assert data['phone'] == '1234567890'
        assert data['created_by'] == self.user.id
        
    def test_created_by_e_read_only(self):
        """Garante que created_by não pode ser sobrescrito via input."""
        outro_user = User.objects.create_user(
            username='outrouser', password='testpassword'
        )
        payload = {
            'name': 'Novo Cliente',
            'email': 'novo@test.com',
            'phone': '0987654321',
            'created_by': outro_user.id,  # Tentativa de sobrescrever created_by
        }
        serializer = ClientSerializer(data=payload)
        
        assert serializer.is_valid(), serializer.errors
        
        # Verifica que o campo created_by não está presente nos dados validados
        assert 'created_by' not in serializer.validated_data
