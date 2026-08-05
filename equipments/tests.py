import pytest
from django.db import IntegrityError, transaction
from django.contrib.auth import get_user_model

from clients.models import Client
from equipments.models import Equipment

User = get_user_model()

pytestmark = pytest.mark.django_db  # aplica acesso ao banco a todos os testes do módulo


@pytest.fixture
def user():
    return User.objects.create_user(username="testuser", password="testpassword")


@pytest.fixture
def client_obj(user):
    return Client.objects.create(
        name="Test Client",
        document="123456789",
        created_by=user,
    )


def test_criacao_encadeada_client_equipment(client_obj):
    equipment = Equipment.objects.create(
        client=client_obj,
        category=Equipment.Category.COMPUTING,
        brand="HP",
        model="ProDesk",
        serial_number="SN-001",
        condition="Bom",
    )
    assert equipment.client == client_obj


def test_serial_number_duplicado_e_recusado(client_obj):
    Equipment.objects.create(
        client=client_obj,
        category=Equipment.Category.COMPUTING,
        brand="HP",
        model="ProDesk",
        serial_number="SN-001",
        condition="Bom",
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Equipment.objects.create(
                client=client_obj,
                category=Equipment.Category.COMPUTING,
                brand="HP",
                model="ProDesk",
                serial_number="SN-001",
                condition="Bom",
            )


def test_multiplos_equipamentos_sem_serial_number(client_obj):
    eqp1 = Equipment.objects.create(
        client=client_obj,
        category=Equipment.Category.COMPUTING,
        brand="HP",
        model="ProDesk",
        serial_number="",
        condition="Usado",
    )
    eqp2 = Equipment.objects.create(
        client=client_obj,
        category=Equipment.Category.COMPUTING,
        brand="HP",
        model="ProDesk",
        serial_number="",
        condition="Usado",
    )
    assert eqp1.serial_number is None
    assert eqp2.serial_number is None
