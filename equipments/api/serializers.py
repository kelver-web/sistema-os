from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from equipments.models import Equipment


class ClientMinimalSerializer(serializers.Serializer):
    """Representação exuta do cliente, só para exibição aninhada de equipamentos."""
    id = serializers.IntegerField()
    name = serializers.CharField()


class EquipmentSerializer(serializers.ModelSerializer):
    client_detail = ClientMinimalSerializer(source="client", read_only=True)
    serial_number = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, default=None
    )

    class Meta:
        model = Equipment
        fields = [
            "id",
            "client",
            "client_detail",
            "category",
            "brand",
            "model",
            "serial_number",
            "accessories",
            "condition",
            "created_at",
        ]
        read_only_fields = ["created_at"]
        validators = [
            UniqueTogetherValidator(
                queryset=Equipment.objects.all(),
                fields=["client", "serial_number"],
                message="Este cliente já possui um equipamento cadastrado com este número de série.",
            )
        ]
