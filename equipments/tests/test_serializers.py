import pytest
from django.contrib.auth import get_user_model
from clients.models import Client
from equipments.models import Equipment
from equipments.api.serializers import EquipmentSerializer


User = get_user_model()


@pytest.mark.django_db
class TestEquipmentSerializer:
    def setup_method(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client_obj = Client.objects.create(
            name="test client",
            email="testclient@teste",
            phone="1234567890",
            created_by=self.user,
        )
        
    def test_serializa_equipment_sem_erro(self):
        equipment = Equipment.objects.create(
            client=self.client_obj,
            category=Equipment.Category.COMPUTING,
            brand="Dell",
            model="XPS 13",
            serial_number="123456789",
            condition="Bom",
        )
        serializer = EquipmentSerializer(equipment)
        data = serializer.data
        
        assert data['brand'] == "Dell"
        assert data['model'] == "XPS 13"
        assert data['serial_number'] == "123456789"
        assert data['condition'] == "Bom"
        assert data['client'] == self.client_obj.id
        
    def test_client_gravavel_e_obrigatorio(self):
        """Diferente de created_by no Client, aqui client DEVE vir do payload."""
        payload = {
            "client": self.client_obj.id,
            "category": "informatica",
            "brand": "Dell",
            "model": "XPS 13",
            "serial_number": "123456789",
            "condition": "Bom",
        }
        serializer = EquipmentSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['client'] == self.client_obj
        
    def test_serial_number_unico_por_cliente(self):
        Equipment.objects.create(
            client=self.client_obj,
            category=Equipment.Category.COMPUTING,
            brand="Dell",
            model="XPS 13",
            serial_number="123456789",
            condition="Bom",
        )
        
        payload = {
            "client": self.client_obj.id,
            "category": "informatica",
            "brand": "Dell",
            "model": "XPS 13",
            "serial_number": "123456789",  # mesmo serial number
            "condition": "Bom",
        }
        serializer = EquipmentSerializer(data=payload)
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors or "serial_number" in serializer.errors