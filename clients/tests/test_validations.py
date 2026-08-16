import pytest
from clients.api.serializers import ClientSerializer


@pytest.mark.django_db
class TestClientDocumentValidation:
    def test_cpf_invalido_retorna_erro_amigavel(self):
        payload = {
            "name": "Teste",
            "email": "teste@x.com",
            "phone": "1",
            "document": "111.111.111-11",  # todos iguais, inválido
        }
        serializer = ClientSerializer(data=payload)
        assert not serializer.is_valid()
        assert "document" in serializer.errors

    def test_cpf_valido_passa(self):
        payload = {
            "name": "Teste",
            "email": "teste2@x.com",
            "phone": "1",
            "document": "111.444.777-35",  # CPF válido conhecido pra teste
        }
        serializer = ClientSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors

    def test_cnpj_invalido_retorna_erro_amigavel(self):
        payload = {
            "name": "Teste",
            "email": "teste@x.com",
            "phone": "1",
            "document": "11.111.111/1111-11",  # todos iguais, inválido
        }
        serializer = ClientSerializer(data=payload)
        assert not serializer.is_valid()
        assert "document" in serializer.errors

    def test_cnpj_valido_passa(self):
        payload = {
            "name": "Teste",
            "email": "teste2@x.com",
            "phone": "1",
            "document": "11.222.333/0001-81",  # CNPJ válido conhecido pra teste
        }
        serializer = ClientSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
