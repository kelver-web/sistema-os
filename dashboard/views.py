from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from accounts.permissions import IsAdmin
from service_orders.models import ServiceOrder


class DashboardView(APIView):
    permission_classes = [IsAdmin]
    
    def get(self, request):
        total_os = ServiceOrder.objects.count()
        por_status = ServiceOrder.objects.values("status").annotate(total=Count("id"))
        os_atrasadas = ServiceOrder.objects.filter(
            deadline__lt=timezone.now(),
            status__in=[ServiceOrder.Status.PENDING, ServiceOrder.Status.IN_PROGRESS], 
        ).count()

        return Response({
            "total_ordens_servico": total_os,
            "por_status": {item["status"]: item["total"] for item in por_status},
            "ordens_atrasadas": os_atrasadas,
        })
        

class DashboardRevenueView(APIView):
    permission_classes = [IsAdmin]
    
    def get(self, request):
        periodo = request.query_params.get("periodo", "30")
        data_limite = timezone.now() - timedelta(days=int(periodo))
        faturamento = ServiceOrder.objects.filter(
            status = ServiceOrder.Status.DELIVERED,
            delivered_at__gte=data_limite,
        ).aggregate(total=Sum("final_cost"))
        
        return Response({
            "periodo_dias": int(periodo),
            "faturamento_total": faturamento["total"] or 0,
        })
