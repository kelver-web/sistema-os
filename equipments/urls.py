from rest_framework.routers import DefaultRouter
from equipments.api.viewsets import EquipmentViewSet

router = DefaultRouter()

router.register("equipments", EquipmentViewSet, basename="equipments")

urlpatterns = router.urls
