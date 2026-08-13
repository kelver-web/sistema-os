from rest_framework.routers import DefaultRouter

from parts.api.viewsets import PartViewSet

router = DefaultRouter()

router.register("parts", PartViewSet, basename="parts")

urlpatterns = router.urls
