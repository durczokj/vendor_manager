"""API URL configuration."""

from django.urls import include, path
from drf_spectacular.views import SpectacularJSONAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.routers import DefaultRouter

from companies.api import CompanyViewSet
from contracts.api import ContractViewSet
from engagements.api import (
    EngagementOrderVersionAssignmentViewSet,
    EngagementUndertakingAssignmentViewSet,
    EngagementViewSet,
)
from leaves.api import LeaveViewSet
from orders.api import OrderVersionViewSet, OrderViewSet
from people.api import PersonViewSet
from undertakings.api import CostCenterViewSet, UndertakingViewSet

router = DefaultRouter()
router.register("companies", CompanyViewSet, basename="companies")
router.register("contracts", ContractViewSet, basename="contracts")
router.register("people", PersonViewSet, basename="people")
router.register("orders", OrderViewSet, basename="orders")
router.register("order-versions", OrderVersionViewSet, basename="order-versions")
router.register("cost-centers", CostCenterViewSet, basename="cost-centers")
router.register("undertakings", UndertakingViewSet, basename="undertakings")
router.register("engagements", EngagementViewSet, basename="engagements")
router.register(
    "engagement-order-version-assignments",
    EngagementOrderVersionAssignmentViewSet,
    basename="engagement-order-version-assignments",
)
router.register(
    "engagement-undertaking-assignments",
    EngagementUndertakingAssignmentViewSet,
    basename="engagement-undertaking-assignments",
)
router.register("leaves", LeaveViewSet, basename="leaves")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "schema/",
        SpectacularJSONAPIView.as_view(permission_classes=[IsAuthenticated]),
        name="schema",
    ),
]
