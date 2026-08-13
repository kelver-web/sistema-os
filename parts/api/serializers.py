from rest_framework import serializers
from parts.models import Part


class PartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Part
        fields = [
            'id', 'name', 'manufacturer', 'model_number', 'supplier',
            'supplier_price', 'sale_price', 'quantity', 'location', 'created_at',
        ]
        read_only_fields = ['created_at']
