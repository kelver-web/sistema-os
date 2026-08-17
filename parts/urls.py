from rest_framework.routers import DefaultRouter

from parts.api.viewsets import PartViewSet, PartMovementViewSet

router = DefaultRouter()

router.register("parts/movements", PartMovementViewSet, basename="parts_movements")
router.register("parts", PartViewSet, basename="parts")

urlpatterns = router.urls
