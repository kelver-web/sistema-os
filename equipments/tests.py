from django.db import IntegrityError, transaction
from django.test import TestCase
from django.contrib.auth import get_user_model

from clients.models import Client
from equipments.models import Equipment

User = get_user_model()


class EquipmentSerialNumberTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.client_obj = Client.objects.create(
            name="Test Client",
            document="123456789",
            created_by=self.user,
        )

    def test_criacao_encadeada_client_equipment(self):
        equipment = Equipment.objects.create(
            client=self.client_obj,
            category=Equipment.Category.COMPUTING,
            brand='HP',
            model='ProDesk',
            serial_number='SN-001',
            condition='Bom',
        )
        self.assertEqual(equipment.client, self.client_obj)
        
    def test_serial_number_duplicado_e_recusado(self):
        Equipment.objects.create(
            client=self.client_obj,
            category=Equipment.Category.COMPUTING,
            brand='HP',
            model='ProDesk',
            serial_number='SN-001',
            condition='Bom',
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Equipment.objects.create(
                    client=self.client_obj,
                    category=Equipment.Category.COMPUTING,
                    brand='HP',
                    model='ProDesk',
                    serial_number='SN-001',
                    condition='Bom',
                )
                
    def test_multiplos_equipamentos_sem_serial_number(self):
        eqp1 = Equipment.objects.create(
            client=self.client_obj,
            category=Equipment.Category.COMPUTING,
            brand='HP',
            model='ProDesk',
            serial_number='',
            condition='Usado',
        )
        eqp2 = Equipment.objects.create(
            client=self.client_obj,
            category=Equipment.Category.COMPUTING,
            brand='HP',
            model='ProDesk',
            serial_number='',
            condition='Usado',
        )
        self.assertIsNone(eqp1.serial_number, '')
        self.assertIsNone(eqp2.serial_number, '')