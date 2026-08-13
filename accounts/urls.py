from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from rest_framework.routers import DefaultRouter
from django.urls import path
from accounts.views import MeView, RegisterView
from accounts.api.viewsets import UserViewSet

router = DefaultRouter()

router.register("users", UserViewSet, basename="users")


urlpatterns = [
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("auth/register/", RegisterView.as_view(), name="register"),
] + router.urls
