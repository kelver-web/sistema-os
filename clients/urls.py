from rest_framework.routers import DefaultRouter

from clients.api.viewsets import ClientViewSet

router = DefaultRouter()

router.register("clients", ClientViewSet, basename="clients")

urlpatterns = router.urls
