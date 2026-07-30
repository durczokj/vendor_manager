"""ViewSets for the engagements app."""

from typing import Any

from rest_framework import serializers as drf_serializers
from rest_framework import viewsets

from engagements.filters import (
    EngagementFilterSet,
    EngagementOrderVersionAssignmentFilterSet,
    EngagementUndertakingAssignmentFilterSet,
)
from engagements.models import Engagement, EngagementOrderVersionAssignment, EngagementUndertakingAssignment
from engagements.serializers import (
    EngagementOrderVersionAssignmentSerializer,
    EngagementSerializer,
    EngagementUndertakingAssignmentSerializer,
)
from engagements.services import update_engagement


class EngagementViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]  # TODO(P8): add type param
    """Engagement list/create/retrieve/update/destroy endpoints."""

    queryset = Engagement.objects.all().order_by("id")
    serializer_class = EngagementSerializer
    filterset_class = EngagementFilterSet
    search_fields: list[str] = []
    ordering_fields = ["id", "start_date", "end_date", "daily_rate", "fte"]

    def get_queryset(self) -> Any:
        """Return engagements accessible to the requesting user."""
        return super().get_queryset().accessible_to(self.request.user)  # type: ignore[attr-defined]

    def perform_update(self, serializer: drf_serializers.BaseSerializer[Any]) -> None:
        """Persist an engagement and adjust child assignment date bounds (FR-15).

        Delegates to the service layer so that undertaking assignment dates are
        clamped to the engagement's new date range on every update.
        """
        engagement: Engagement = serializer.instance  # type: ignore[assignment]
        for attr, value in serializer.validated_data.items():
            setattr(engagement, attr, value)
        update_engagement(engagement=engagement)


class EngagementOrderVersionAssignmentViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]  # TODO(P8): add type param
    """EngagementOrderVersionAssignment list/create/retrieve/update/destroy endpoints."""

    queryset = EngagementOrderVersionAssignment.objects.all().order_by("id")
    serializer_class = EngagementOrderVersionAssignmentSerializer
    filterset_class = EngagementOrderVersionAssignmentFilterSet
    search_fields: list[str] = []
    ordering_fields = ["id"]

    def get_queryset(self) -> Any:
        """Return engagement–order-version assignments accessible to the requesting user."""
        return super().get_queryset().accessible_to(self.request.user)  # type: ignore[attr-defined]


class EngagementUndertakingAssignmentViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]  # TODO(P8): add type param
    """EngagementUndertakingAssignment list/create/retrieve/update/destroy endpoints."""

    queryset = EngagementUndertakingAssignment.objects.all().order_by("id")
    serializer_class = EngagementUndertakingAssignmentSerializer
    filterset_class = EngagementUndertakingAssignmentFilterSet
    search_fields: list[str] = []
    ordering_fields = ["id", "start_date", "end_date", "percentage"]

    def get_queryset(self) -> Any:
        """Return engagement–undertaking assignments accessible to the requesting user."""
        return super().get_queryset().accessible_to(self.request.user)  # type: ignore[attr-defined]
