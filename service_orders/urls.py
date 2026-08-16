from rest_framework.routers import DefaultRouter

from service_orders.api.viewsets import ServiceOrderViewSet

router = DefaultRouter()

router.register("service-orders", ServiceOrderViewSet, basename="service_orders")

urlpatterns = router.urls
