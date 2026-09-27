"""
Testes do service de transição de status e da timeline.

Cobrem três garantias:

1. Toda mudança de status grava exatamente uma entrada na timeline
2. Transição inválida não muda status nem grava timeline
3. Status e timeline são atômicos: se a timeline falha, o status não muda
"""

import pytest
from django.contrib.auth import get_user_model
from django.db import DatabaseError
from rest_framework import status
from rest_framework.test import APIClient

from clients.models import Client
from equipments.models import Equipment
from service_orders.models import ServiceOrder, ServiceTimeLine
from service_orders.services import (
    TransicaoInvalida,
    registrar_transicao,
)

User = get_user_model()
Status = ServiceOrder.Status


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="admin_svc",
        email="admin_svc@teste.com",
        password="senha123",
        role=User.Role.ADMIN,
        is_staff=True,
    )


@pytest.fixture
def tech_user(db):
    return User.objects.create_user(
        username="tech_svc",
        email="tech_svc@teste.com",
        password="senha123",
        role=User.Role.TECH,
    )


@pytest.fixture
def attendant_user(db):
    return User.objects.create_user(
        username="attendant_svc",
        email="attendant_svc@teste.com",
        password="senha123",
        role=User.Role.ATTENDANT,
    )


@pytest.fixture
def os_pendente(admin_user):
    cliente = Client.objects.create(
        name="Cliente Timeline",
        email="cliente_timeline@teste.com",
        phone="84999991111",
        created_by=admin_user,
    )
    equipamento = Equipment.objects.create(
        client=cliente,
        category="informatica",
        brand="Dell",
        model="XPS",
        serial_number="TL-001",
    )
    ordem = ServiceOrder.objects.create(
        client=cliente,
        equipment=equipamento,
        opened_by=admin_user,
        reported_problem="Não liga",
    )
    return ordem


@pytest.fixture
def api_tech(tech_user):
    client = APIClient()
    client.force_authenticate(user=tech_user)
    return client


@pytest.fixture
def api_admin(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def api_attendant(attendant_user):
    client = APIClient()
    client.force_authenticate(user=attendant_user)
    return client


class TestTimelineEAutomatica:
    """A timeline nasce junto com a mudança de status, sem chamada explícita do
    developer no view."""

    def test_abrir_os_registra_evento_de_criacao(
        self, api_tech, os_pendente, tech_user
    ):
        ordem = ServiceOrder.objects.get(pk=os_pendente.pk)
        assert ordem.timeline.count() == 0

        resp = api_tech.post(
            "/api/service-orders/",
            {
                "client": os_pendente.client_id,
                "equipment": os_pendente.equipment_id,
                "reported_problem": "Tela quebrada",
            },
        )

        assert resp.status_code == status.HTTP_201_CREATED
        assert ServiceTimeLine.objects.filter(
            service_order_id=resp.data["id"], action="created"
        ).exists()

    def test_transicao_valida_gera_exatamente_uma_entrada(self, os_pendente, tech_user):
        registrar_transicao(
            os_pendente, Status.IN_PROGRESS, tech_user, descricao="Técnico assumiu"
        )

        assert os_pendente.status == Status.IN_PROGRESS
        assert os_pendente.timeline.count() == 1

        entrada = os_pendente.timeline.first()
        assert entrada.action == "status_change"
        assert entrada.user == tech_user
        assert entrada.description == "Técnico assumiu"

    def test_transicao_invalida_nao_muda_status_nem_grava_timeline(
        self, os_pendente, tech_user
    ):
        with pytest.raises(TransicaoInvalida):
            registrar_transicao(os_pendente, Status.DELIVERED, tech_user)

        os_pendente.refresh_from_db()
        assert os_pendente.status == Status.PENDING
        assert os_pendente.timeline.count() == 0

    def test_timestamp_preenchido_ao_alcancar_in_progress(self, os_pendente, tech_user):
        assert os_pendente.started_at is None

        registrar_transicao(os_pendente, Status.IN_PROGRESS, tech_user)

        os_pendente.refresh_from_db()
        assert os_pendente.started_at is not None

    def test_timestamp_preenchido_ao_alcancar_completed(self, os_pendente, tech_user):
        registrar_transicao(os_pendente, Status.IN_PROGRESS, tech_user)
        registrar_transicao(os_pendente, Status.COMPLETED, tech_user)

        os_pendente.refresh_from_db()
        assert os_pendente.completed_at is not None

    def test_descricao_padrao_quando_nao_informada(self, os_pendente, tech_user):
        registrar_transicao(os_pendente, Status.IN_PROGRESS, tech_user)

        entrada = os_pendente.timeline.first()
        assert Status.IN_PROGRESS in entrada.description

    def test_caminho_completo_gera_uma_entrada_por_transicao(
        self, os_pendente, admin_user
    ):
        registrar_transicao(os_pendente, Status.IN_PROGRESS, admin_user)
        registrar_transicao(os_pendente, Status.AWAITING_APPROVAL, admin_user)
        registrar_transicao(os_pendente, Status.COMPLETED, admin_user)
        registrar_transicao(os_pendente, Status.DELIVERED, admin_user)

        assert os_pendente.timeline.count() == 4
        assert os_pendente.status == Status.DELIVERED


class TestAtomicidade:
    """Status e timeline andam juntos."""

    def test_status_nao_muda_se_timeline_falhar(
        self, os_pendente, tech_user, monkeypatch
    ):
        def explode(*args, **kwargs):
            raise DatabaseError("timeline fora do ar")

        monkeypatch.setattr(
            "service_orders.services.ServiceTimeLine.objects.create", explode
        )

        with pytest.raises(DatabaseError):
            registrar_transicao(os_pendente, Status.IN_PROGRESS, tech_user)

        os_pendente.refresh_from_db()
        assert os_pendente.status == Status.PENDING, "status não pode ter mudado"
        assert os_pendente.started_at is None


class TestTransicionarAPI:
    """A action HTTP e o bloqueio do PATCH."""

    def test_transicao_valida_pela_api(self, api_tech, os_pendente):
        resp = api_tech.post(
            f"/api/service-orders/{os_pendente.pk}/transicionar/",
            {"status": Status.IN_PROGRESS},
            format="json",
        )

        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["status"] == Status.IN_PROGRESS

    def test_transicao_invalida_retorna_400_com_contexto(self, api_tech, os_pendente):
        resp = api_tech.post(
            f"/api/service-orders/{os_pendente.pk}/transicionar/",
            {"status": Status.DELIVERED},
            format="json",
        )

        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.data["status_atual"] == Status.PENDING
        assert resp.data["status_desejado"] == Status.DELIVERED
        assert os_pendente.timeline.count() == 0

    def test_status_inexistente_retorna_400_com_lista_de_validos(
        self, api_tech, os_pendente
    ):
        resp = api_tech.post(
            f"/api/service-orders/{os_pendente.pk}/transicionar/",
            {"status": "STATUS_FANTASMA"},
            format="json",
        )

        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "status_validos" in resp.data

    def test_status_ausente_retorna_400(self, api_tech, os_pendente):
        resp = api_tech.post(
            f"/api/service-orders/{os_pendente.pk}/transicionar/",
            {},
            format="json",
        )

        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_com_status_e_recusado(self, api_tech, os_pendente):
        resp = api_tech.patch(
            f"/api/service-orders/{os_pendente.pk}/",
            {"status": Status.DELIVERED},
            format="json",
        )

        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "transicionar" in resp.data["detail"]

        os_pendente.refresh_from_db()
        assert os_pendente.status == Status.PENDING

    def test_patch_sem_status_continua_funcionando(self, api_tech, os_pendente):
        resp = api_tech.patch(
            f"/api/service-orders/{os_pendente.pk}/",
            {"technical_findings": "Fonte queimada"},
            format="json",
        )

        assert resp.status_code == status.HTTP_200_OK
        os_pendente.refresh_from_db()
        assert os_pendente.technical_findings == "Fonte queimada"

    def test_tecnico_nao_conclui_os_em_aguardando_aprovacao(
        self, api_tech, os_pendente, tech_user
    ):
        registrar_transicao(os_pendente, Status.IN_PROGRESS, tech_user)
        registrar_transicao(os_pendente, Status.AWAITING_APPROVAL, tech_user)

        resp = api_tech.post(
            f"/api/service-orders/{os_pendente.pk}/transicionar/",
            {"status": Status.COMPLETED},
            format="json",
        )

        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_atendente_conclui_os_em_aguardando_aprovacao(
        self, api_attendant, os_pendente, tech_user
    ):
        registrar_transicao(os_pendente, Status.IN_PROGRESS, tech_user)
        registrar_transicao(os_pendente, Status.AWAITING_APPROVAL, tech_user)

        resp = api_attendant.post(
            f"/api/service-orders/{os_pendente.pk}/transicionar/",
            {"status": Status.COMPLETED},
            format="json",
        )

        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["status"] == Status.COMPLETED


class TestTimelineEndpoint:
    def test_timeline_lista_eventos_em_ordem_cronologica(
        self, api_tech, os_pendente, tech_user
    ):
        registrar_transicao(
            os_pendente, Status.IN_PROGRESS, tech_user, descricao="primeiro"
        )
        registrar_transicao(
            os_pendente, Status.AWAITING_PARTS, tech_user, descricao="segundo"
        )

        resp = api_tech.get(f"/api/service-orders/{os_pendente.pk}/timeline/")

        assert resp.status_code == status.HTTP_200_OK
        assert [e["description"] for e in resp.data["results"]] == [
            "primeiro",
            "segundo",
        ]
