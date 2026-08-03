from rest_framework import serializers

from clients.models import Client


class ClientSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Client
        fields = [
            'id', 'name', 'email', 'phone',
            'address', 'document', 'notes',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
