# service_orders/tests/test_permissions.py
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from clients.models import Client
from equipments.models import Equipment
from service_orders.models import ServiceOrder

User = get_user_model()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="admin_esc",
        email="admin_esc@teste.com",
        password="senha123",
        role=User.Role.ADMIN,
        is_staff=True,
    )


@pytest.fixture
def tech_user(db):
    return User.objects.create_user(
        username="tech_esc",
        email="tech_esc@teste.com",
        password="senha123",
        role=User.Role.TECH,
    )


@pytest.fixture
def attendant_user(db):
    return User.objects.create_user(
        username="attendant_esc",
        email="attendant_esc@teste.com",
        password="senha123",
        role=User.Role.ATTENDANT,
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
        client=base_client_obj,
        category="informatica",
        brand="Dell",
        model="X",
        condition="ok",
        serial_number="ESC-001",
    )


def client_para(user):  # mock para simular request
    api = APIClient()
    api.force_authenticate(user=user)
    return api


@pytest.mark.django_db
class TestEscalonamentoDePermissao:
    def test_attendant_nao_consegue_se_auto_atribuir_como_tecnico(
        self, attendant_user, base_client_obj, base_equipment
    ):
        """
        Tenta burlar a permissão: attendant abre uma OS e tenta se
        atribuir como technician diretamente no payload de criação,
        sem passar pela action 'assumir' (que é a única via permitida).
        """
        api = client_para(attendant_user)

        resp = api.post(
            "/api/service-orders/",
            {
                "client": base_client_obj.id,
                "equipment": base_equipment.id,
                "reported_problem": "Teste de escalonamento",
                "technician": attendant_user.id,  # tentativa de forjar
            },
        )

        assert resp.status_code == status.HTTP_201_CREATED

        service_order = ServiceOrder.objects.get(id=resp.data["id"])
        assert service_order.technician is None, (
            "FALHA DE SEGURANÇA: attendant conseguiu se auto-atribuir "
            "como técnico via payload de criação da OS."
        )

    def test_attendant_nao_consegue_mudar_status_direto_no_payload(
        self, attendant_user, base_client_obj, base_equipment
    ):
        """
        Outra tentativa de burlar: mandar status=COMPLETED direto na
        criação, pulando todo o fluxo (assumir -> concluir).
        """
        api = client_para(attendant_user)

        resp = api.post(
            "/api/service-orders/",
            {
                "client": base_client_obj.id,
                "equipment": base_equipment.id,
                "reported_problem": "Teste de status forjado",
                "status": ServiceOrder.Status.COMPLETED,
            },
        )

        assert resp.status_code == status.HTTP_201_CREATED

        service_order = ServiceOrder.objects.get(id=resp.data["id"])
        assert service_order.status == ServiceOrder.Status.PENDING, (
            "FALHA DE SEGURANÇA: status foi definido direto pelo payload, "
            "pulando o fluxo de assumir/concluir."
        )

    def test_attendant_nao_consegue_forjar_opened_by(
        self, attendant_user, tech_user, base_client_obj, base_equipment
    ):
        """
        Confirma que opened_by continua vindo do request.user,
        nunca do payload — mesmo já validado antes, vale reconfirmar
        no mesmo teste de escalonamento.
        """
        api = client_para(attendant_user)

        resp = api.post(
            "/api/service-orders/",
            {
                "client": base_client_obj.id,
                "equipment": base_equipment.id,
                "reported_problem": "Teste opened_by forjado",
                "opened_by": tech_user.id,  # tentando forjar autoria
            },
        )

        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["opened_by"] == attendant_user.id

    def test_tech_pode_ser_atribuido_apenas_via_action_assumir(
        self, tech_user, base_client_obj, base_equipment
    ):
        """
        Controle positivo: confirma que o único caminho legítimo pra
        preencher 'technician' é a action assumir, não o payload direto.
        """
        api = client_para(tech_user)

        resp = api.post(
            "/api/service-orders/",
            {
                "client": base_client_obj.id,
                "equipment": base_equipment.id,
                "reported_problem": "Fluxo correto",
            },
        )
        os_id = resp.data["id"]

        service_order = ServiceOrder.objects.get(id=os_id)
        assert service_order.technician is None

        resp = api.post(f"/api/service-orders/{os_id}/assumir/")
        assert resp.status_code == status.HTTP_200_OK

        service_order.refresh_from_db()
        assert service_order.technician == tech_user
        assert service_order.status == ServiceOrder.Status.IN_PROGRESS
