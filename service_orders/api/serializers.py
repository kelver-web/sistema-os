from rest_framework import serializers
from service_orders.models import ServiceOrder


class ServiceOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceOrder
        fields = [
             'id', 'client', 'equipment', 'opened_by', 'technician',
            'reported_problem', 'technical_fidings', 'solution_description',
            'status', 'priority', 'estimated_cost', 'final_cost',
            'opened_at', 'started_at', 'completed_at', 'delivered_at', 'deadline',
        ]
        read_only_fields = ['opened_by', 'status', 'started_at', 'completed_at', 'opened_at']
