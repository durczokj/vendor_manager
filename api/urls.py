"""API URL configuration."""

from django.urls import include, path
from drf_spectacular.views import SpectacularJSONAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.routers import DefaultRouter

from .viewsets import CompanyViewSet

router = DefaultRouter()
router.register("companies", CompanyViewSet, basename="companies")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "schema/",
        SpectacularJSONAPIView.as_view(permission_classes=[IsAuthenticated]),
        name="schema",
    ),
]
