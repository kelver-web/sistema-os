from rest_framework import serializers
from service_orders.models import ServiceOrder, ServiceOrderItem, ServiceTimeLine


class ServiceOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceOrder
        fields = [
            "id",
            "client",
            "equipment",
            "opened_by",
            "technician",
            "reported_problem",
            "technical_findings",
            "solution_description",
            "status",
            "priority",
            "estimated_cost",
            "final_cost",
            "opened_at",
            "started_at",
            "completed_at",
            "delivered_at",
            "deadline",
        ]
        read_only_fields = [
            "opened_by",
            "status",
            "technician",
            "started_at",
            "completed_at",
            "opened_at",
        ]


class ServiceOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceOrderItem
        fields = [
            "id",
            "service_order",
            "description",
            "quantity",
            "unit_price",
            "total",
        ]
        read_only_fields = ["service_order", "total"]


class ServiceTimeLineSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(
        source="user.get_full_name", read_only=True, default=""
    )
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = ServiceTimeLine
        fields = [
            "id",
            "action",
            "description",
            "user",
            "user_name",
            "username",
            "created_at",
        ]
        read_only_fields = ["user", "created_at"]
