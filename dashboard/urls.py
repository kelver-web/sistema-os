from django.urls import path
from .views import DashboardView, DashboardRevenueView


urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("dashboard/revenue/", DashboardRevenueView.as_view(), name="dashboard-revenue"),
]
