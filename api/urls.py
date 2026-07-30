"""API URL configuration."""

from django.urls import include, path
from drf_spectacular.views import SpectacularJSONAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from companies.api import CompanyViewSet
from contracts.api import ContractViewSet
from dashboards.api import DashboardEntityOptionsView, DashboardSummaryView
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

# Nested router: /api/v1/engagements/<engagement_pk>/…
engagements_router = NestedDefaultRouter(router, "engagements", lookup="engagement")
engagements_router.register(
    "undertaking-assignments",
    EngagementUndertakingAssignmentViewSet,
    basename="engagements-undertaking-assignments",
)
engagements_router.register(
    "order-version-assignments",
    EngagementOrderVersionAssignmentViewSet,
    basename="engagements-order-version-assignments",
)

urlpatterns = [
    path("", include(router.urls)),
    path("", include(engagements_router.urls)),
    path("dashboards/summary/", DashboardSummaryView.as_view(), name="dashboards-summary"),
    path("dashboards/entity-options/", DashboardEntityOptionsView.as_view(), name="dashboards-entity-options"),
    path(
        "schema/",
        SpectacularJSONAPIView.as_view(permission_classes=[IsAuthenticated]),
        name="schema",
    ),
]
