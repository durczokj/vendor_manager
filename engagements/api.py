"""ViewSets for the engagements app."""

from typing import Any, cast

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import serializers as drf_serializers
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from engagements.filters import (
    EngagementFilterSet,
    EngagementOrderVersionAssignmentFilterSet,
    EngagementUndertakingAssignmentFilterSet,
)
from engagements.managers import (
    EngagementOrderVersionAssignmentQuerySet,
    EngagementQuerySet,
    EngagementUndertakingAssignmentQuerySet,
)
from engagements.models import Engagement, EngagementOrderVersionAssignment, EngagementUndertakingAssignment
from engagements.selectors import engagement_cost_coverage, engagement_costs
from engagements.serializers import (
    EngagementOrderVersionAssignmentSerializer,
    EngagementSerializer,
    EngagementUndertakingAssignmentSerializer,
)
from engagements.services import update_engagement


class EngagementViewSet(viewsets.ModelViewSet[Engagement]):
    """Engagement list/create/retrieve/update/destroy endpoints."""

    queryset = Engagement.objects.all().order_by("id")
    serializer_class = EngagementSerializer
    filterset_class = EngagementFilterSet
    search_fields: list[str] = []
    ordering_fields = ["id", "start_date", "end_date", "daily_rate", "fte"]

    def get_queryset(self) -> EngagementQuerySet:
        """Return engagements accessible to the requesting user."""
        assert self.request.user.is_authenticated
        return Engagement.objects.accessible_to(self.request.user).order_by("id")

    def perform_update(self, serializer: drf_serializers.BaseSerializer[Any]) -> None:
        """Persist an engagement and adjust child assignment date bounds (FR-15).

        Delegates to the service layer so that undertaking assignment dates are
        clamped to the engagement's new date range on every update.
        """
        engagement = cast(Engagement, serializer.instance)
        for attr, value in serializer.validated_data.items():
            setattr(engagement, attr, value)
        update_engagement(engagement=engagement)

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        summary="Day-level cost breakdown for an engagement",
        description=(
            "Returns a list of {date, cost} records covering the engagement's full date range. "
            "Cost is zero on days the engagement is not covered by an active order version or when "
            "the person is on leave."
        ),
    )
    @action(detail=True, methods=["get"], url_path="costs")
    def costs(self, request: Request, pk: Any = None) -> Response:
        """Return day-level cost rows for the engagement (FR-31).

        Args:
            request: The incoming DRF request.
            pk: The primary key of the Engagement.

        Returns:
            200 with a list of {date, cost} dicts.

        """
        engagement: Engagement = self.get_object()
        rows = engagement_costs(engagement)
        return Response([{"date": str(row["date"])[:10], "cost": float(row["cost"])} for row in rows])

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        summary="Day-level undertaking cost-coverage for an engagement",
        description=(
            "Returns a list of {date, undertaking, percentage} records showing how each active day "
            "of the engagement is covered by undertaking assignments. "
            "Days with under-coverage are included with undertaking=null."
        ),
    )
    @action(detail=True, methods=["get"], url_path="cost-coverage")
    def cost_coverage(self, request: Request, pk: Any = None) -> Response:
        """Return day-level undertaking coverage rows for the engagement (FR-31).

        Args:
            request: The incoming DRF request.
            pk: The primary key of the Engagement.

        Returns:
            200 with a list of {date, undertaking, percentage} dicts.

        """
        engagement: Engagement = self.get_object()
        rows = engagement_cost_coverage(engagement)
        return Response(
            [
                {
                    "date": str(row["date"])[:10],
                    "undertaking": row["undertaking"].pk if row["undertaking"] is not None else None,
                    "percentage": float(row["percentage"]),
                }
                for row in rows
            ]
        )


class EngagementOrderVersionAssignmentViewSet(viewsets.ModelViewSet[EngagementOrderVersionAssignment]):
    """EngagementOrderVersionAssignment list/create/retrieve/update/destroy endpoints."""

    queryset = EngagementOrderVersionAssignment.objects.all().order_by("id")
    serializer_class = EngagementOrderVersionAssignmentSerializer
    filterset_class = EngagementOrderVersionAssignmentFilterSet
    search_fields: list[str] = []
    ordering_fields = ["id"]

    def get_queryset(self) -> EngagementOrderVersionAssignmentQuerySet:
        """Return engagement–order-version assignments accessible to the requesting user.

        When called from the nested route the queryset is additionally scoped to
        the parent engagement identified by ``engagement_pk``.
        """
        assert self.request.user.is_authenticated
        qs = EngagementOrderVersionAssignment.objects.accessible_to(self.request.user).order_by("id")
        engagement_pk = self.kwargs.get("engagement_pk")
        if engagement_pk is not None:
            qs = qs.filter(engagement_id=engagement_pk)
        return qs


class EngagementUndertakingAssignmentViewSet(viewsets.ModelViewSet[EngagementUndertakingAssignment]):
    """EngagementUndertakingAssignment list/create/retrieve/update/destroy endpoints."""

    queryset = EngagementUndertakingAssignment.objects.all().order_by("id")
    serializer_class = EngagementUndertakingAssignmentSerializer
    filterset_class = EngagementUndertakingAssignmentFilterSet
    search_fields: list[str] = []
    ordering_fields = ["id", "start_date", "end_date", "percentage"]

    def get_queryset(self) -> EngagementUndertakingAssignmentQuerySet:
        """Return engagement–undertaking assignments accessible to the requesting user.

        When called from the nested route the queryset is additionally scoped to
        the parent engagement identified by ``engagement_pk``.
        """
        assert self.request.user.is_authenticated
        qs = EngagementUndertakingAssignment.objects.accessible_to(self.request.user).order_by("id")
        engagement_pk = self.kwargs.get("engagement_pk")
        if engagement_pk is not None:
            qs = qs.filter(engagement_id=engagement_pk)
        return qs
