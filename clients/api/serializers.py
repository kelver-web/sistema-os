from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from clients.models import Client

from clients.validators import validate_document


class ClientSerializer(serializers.ModelSerializer):
    document = serializers.CharField(  # CNPJ ou CPF
        required=False, allow_blank=True, validators=[validate_document]
    )
    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=Client.objects.all(),
                message="Já existe um cliente cadastrado com este e-mail.",
            )
        ]
    )

    class Meta:
        model = Client
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "address",
            "document",
            "notes",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_by", "created_at", "updated_at"]
