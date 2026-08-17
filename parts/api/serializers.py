from rest_framework import serializers
from parts.models import Part, PartMovement


class PartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Part
        fields = [
            "id",
            "name",
            "manufacturer",
            "model_number",
            "supplier",
            "supplier_price",
            "sale_price",
            "quantity",
            "location",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class PartMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartMovement
        fields = [
            'id', 'part', 'service_order', 'movement_type',
            'quantity', 'unit_price', 'notes', 'created_by', 'created_at',
        ]
        read_only_fields = ['created_by', 'created_at']

