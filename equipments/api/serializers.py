from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from equipments.models import Equipment


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = [
            "id",
            "client",
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
