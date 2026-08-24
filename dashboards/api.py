"""API views for the dashboards app.

Exposes three endpoints:

* ``GET|POST /api/v1/dashboards/summary/`` — pre-aggregated cost series for
  the dashboard UI. Delegates to :func:`dashboards.services.build_summary`.
* ``GET|POST /api/v1/dashboards/cost-lines/`` — unaggregated day-level cost
  rows with denormalized display names, intended for LLM / MCP / export
  clients. Delegates to :func:`dashboards.services.build_cost_lines`.
* ``GET /api/v1/dashboards/entity-options/`` — the lists of entities
  accessible to the requesting user, used to populate the dashboard filter
  dropdowns (FR-43, FR-46).
"""

from __future__ import annotations

from datetime import date
from typing import Any, cast

from django.contrib.auth.models import User
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from companies.models import Company
from dashboards.services import (
    VALID_CLASSES,
    VALID_GRANULARITIES,
    CostLinesSpanTooLargeError,
    build_cost_lines,
    build_summary,
)
from engagements.models import Engagement
from orders.models import Order
from people.models import Person
from undertakings.models import Undertaking


class _CostFilterSerializer(serializers.Serializer[Any]):
    """Shared filter fields for cost-based endpoints.

    Serves as the common base for endpoints that start from
    :func:`dashboards.selectors.get_accessible_cost_rows`.  Concrete
    serializers add or tighten fields as needed (e.g.
    :class:`_SummaryRequestSerializer` adds ``class_`` and ``granularity``;
    :class:`_CostLinesRequestSerializer` marks ``date_from`` / ``date_to`` as
    required).
    """

    date_from = serializers.DateField(
        required=False,
        allow_null=True,
        default=None,
        help_text="Inclusive lower bound on the cost date (YYYY-MM-DD).",
    )
    date_to = serializers.DateField(
        required=False,
        allow_null=True,
        default=None,
        help_text="Inclusive upper bound on the cost date (YYYY-MM-DD).",
    )
    person_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        help_text="Restrict to these Person primary keys.  Empty list means no restriction.",
    )
    order_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
        help_text="Restrict to these Order primary keys.  Empty list means no restriction.",
    )
    company_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
        help_text="Restrict to these Company primary keys.  Empty list means no restriction.",
    )
    undertaking_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
        help_text="Restrict to these Undertaking primary keys.  Empty list means no restriction.",
    )
    engagement_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
        help_text="Restrict to these Engagement primary keys.  Empty list means no restriction.",
    )


class _SummaryRequestSerializer(_CostFilterSerializer):
    """Deserialises and validates the dashboard summary filter parameters.

    All fields are optional; the service applies sensible defaults (no
    restriction) when they are omitted.
    """

    class_ = serializers.ChoiceField(
        choices=sorted(VALID_CLASSES),
        default="Person",
        help_text="Entity class to group costs by.",
    )
    granularity = serializers.ChoiceField(
        choices=sorted(VALID_GRANULARITIES),
        default="Total",
        help_text="Time-bucket granularity for aggregation.",
    )


class _CostLinesRequestSerializer(_CostFilterSerializer):
    """Deserialises and validates cost-lines filter parameters.

    ``date_from`` and ``date_to`` are mandatory; the service caps the span at
    ``settings.DASHBOARDS_COST_LINES_MAX_DAYS`` and returns HTTP 400 above it.
    """

    date_from = serializers.DateField(
        required=True,
        help_text="Inclusive lower bound on the cost date (YYYY-MM-DD). Required.",
    )
    date_to = serializers.DateField(
        required=True,
        help_text="Inclusive upper bound on the cost date (YYYY-MM-DD). Required.",
    )


class _SummaryRowSerializer(serializers.Serializer[Any]):
    """Represents a single aggregated row in the summary response."""

    id = serializers.JSONField(
        allow_null=True,
        help_text="Primary key of the entity (None for unassigned rows).",
    )
    name = serializers.CharField(help_text="Human-readable display name for the entity.")
    cost = serializers.FloatField(help_text="Aggregated cost for this entity/time bucket.")
    date = serializers.CharField(
        allow_null=True,
        help_text="ISO date string (YYYY-MM-DD) when granularity=Daily, else null.",
    )
    month = serializers.CharField(
        allow_null=True,
        help_text="Month string (YYYY-MM) when granularity=Monthly, else null.",
    )


class _SummaryResponseSerializer(serializers.Serializer[Any]):
    """Represents the full dashboard summary response payload."""

    class_ = serializers.CharField(help_text="The entity class that was used for grouping.")
    granularity = serializers.CharField(help_text="The granularity that was used for aggregation.")
    rows = _SummaryRowSerializer(many=True, help_text="Aggregated cost rows.")


def _entity_selection_from_params(params: dict[str, Any]) -> dict[str, list[Any]]:
    """Build the ``entity_selection`` dict expected by ``build_summary``.

    Args:
        params: Validated data from :class:`_SummaryRequestSerializer`.

    Returns:
        A mapping of entity class names to lists of primary-key values.
    """
    return {
        "Person": params["person_ids"],
        "Order": params["order_ids"],
        "Company": params["company_ids"],
        "Undertaking": params["undertaking_ids"],
        "Engagement": params["engagement_ids"],
    }


_SUMMARY_DESCRIPTION = (
    "Returns pre-aggregated cost series data and a tabular breakdown for the "
    "dashboard.  All results are scoped to entities accessible to the "
    "requesting user (FR-45).  The GET variant accepts all filter parameters "
    "as query-string parameters; the POST variant accepts them in the request "
    "body as JSON."
)

_SUMMARY_EXAMPLES = [
    OpenApiExample(
        "Total cost by person",
        value={
            "class_": "Person",
            "granularity": "Total",
            "date_from": None,
            "date_to": None,
            "person_ids": [],
            "order_ids": [],
            "company_ids": [],
            "undertaking_ids": [],
            "engagement_ids": [],
        },
        request_only=True,
    ),
]


@extend_schema(
    summary="Dashboard summary (GET)",
    description=_SUMMARY_DESCRIPTION,
    parameters=[_SummaryRequestSerializer],
    responses={200: _SummaryResponseSerializer},
    examples=_SUMMARY_EXAMPLES,
    tags=["dashboards"],
)
class DashboardSummaryView(APIView):
    """GET/POST ``/api/v1/dashboards/summary/``.

    Both verbs delegate to :func:`dashboards.services.build_summary` after
    validating the filter parameters.  GET passes parameters via the query
    string; POST passes them in the JSON body.
    """

    def _run(self, data: Any) -> Response:
        """Validate *data*, call the service, and return the HTTP response.

        Args:
            data: Raw input dict (from query params or request body).

        Returns:
            200 response with the serialised :data:`~dashboards.services.SummaryPayload`.
            400 response when input validation fails.
        """
        req_ser = _SummaryRequestSerializer(data=data)
        if not req_ser.is_valid():
            return Response(req_ser.errors, status=400)

        params = req_ser.validated_data
        date_from: date | None = params["date_from"]
        date_to: date | None = params["date_to"]

        payload = build_summary(
            user=cast(User, self.request.user),
            class_=params["class_"],
            granularity=params["granularity"],
            date_range=(date_from, date_to),
            entity_selection=_entity_selection_from_params(params),
        )

        resp_ser = _SummaryResponseSerializer(payload)
        return Response(resp_ser.data)

    def get(self, request: Request) -> Response:
        """Handle ``GET /api/v1/dashboards/summary/``.

        Args:
            request: The incoming DRF request.  Filter parameters are read
                from the query string.

        Returns:
            200 with the summary payload, or 400 on validation failure.
        """
        return self._run(request.query_params)

    @extend_schema(
        summary="Dashboard summary (POST)",
        description=_SUMMARY_DESCRIPTION,
        request=_SummaryRequestSerializer,
        responses={200: _SummaryResponseSerializer},
        examples=_SUMMARY_EXAMPLES,
        tags=["dashboards"],
    )
    def post(self, request: Request) -> Response:
        """Handle ``POST /api/v1/dashboards/summary/``.

        Args:
            request: The incoming DRF request.  Filter parameters are read
                from the JSON request body.

        Returns:
            200 with the summary payload, or 400 on validation failure.
        """
        return self._run(dict(request.data))


class _EntityOptionSerializer(serializers.Serializer[Any]):
    """Represents a single selectable entity option."""

    id = serializers.JSONField(help_text="Primary key of the entity.")
    name = serializers.CharField(help_text="Human-readable display name.")


class _EntityOptionsResponseSerializer(serializers.Serializer[Any]):
    """Represents the entity options response payload."""

    persons = _EntityOptionSerializer(many=True, help_text="Persons accessible to the requesting user.")
    companies = _EntityOptionSerializer(many=True, help_text="Companies accessible to the requesting user.")
    orders = _EntityOptionSerializer(many=True, help_text="Orders accessible to the requesting user.")
    undertakings = _EntityOptionSerializer(many=True, help_text="Undertakings accessible to the requesting user.")
    engagements = _EntityOptionSerializer(many=True, help_text="Engagements accessible to the requesting user.")


@extend_schema(
    summary="Dashboard entity options",
    description=(
        "Returns lists of entities accessible to the requesting user (FR-43, FR-46). "
        "Use this endpoint to populate dashboard filter dropdowns; it always respects "
        "the caller's role scope via accessible_to(user) — never returns a full list."
    ),
    responses={200: _EntityOptionsResponseSerializer},
    tags=["dashboards"],
)
class DashboardEntityOptionsView(APIView):
    """GET ``/api/v1/dashboards/entity-options/``.

    Returns the accessible entity lists used to populate the dashboard
    filter dropdowns.  Every queryset is scoped via ``accessible_to(user)``
    so callers only see entities within their role scope.
    """

    def get(self, request: Request) -> Response:
        """Handle ``GET /api/v1/dashboards/entity-options/``.

        Args:
            request: The incoming DRF request.

        Returns:
            200 response with lists of accessible entities grouped by type.
        """
        user = cast(User, request.user)

        persons = [
            {"id": p.pk, "name": str(p)} for p in Person.objects.accessible_to(user).order_by("last_name", "first_name")
        ]
        companies = [{"id": c.pk, "name": str(c)} for c in Company.objects.accessible_to(user).order_by("name")]
        orders = [{"id": o.pk, "name": o.name} for o in Order.objects.accessible_to(user).order_by("name")]
        undertakings = [{"id": u.pk, "name": str(u)} for u in Undertaking.objects.accessible_to(user).order_by("name")]
        engagements = [
            {"id": e.pk, "name": f"Engagement {e.pk}"} for e in Engagement.objects.accessible_to(user).order_by("pk")
        ]

        payload = {
            "persons": persons,
            "companies": companies,
            "orders": orders,
            "undertakings": undertakings,
            "engagements": engagements,
        }
        resp_ser = _EntityOptionsResponseSerializer(payload)
        return Response(resp_ser.data)


class _CostLineRowSerializer(serializers.Serializer[Any]):
    """A single day-level cost row in the cost-lines response.

    Every dimension (person, order, company, undertaking) is present on every
    row, along with the cost components (``daily_rate``, ``fte``,
    ``percentage``, ``is_working_day``), so clients can reconcile invoice
    lines without any follow-up requests.
    """

    date = serializers.DateField(help_text="Cost date (YYYY-MM-DD).")
    cost = serializers.FloatField(help_text="Cost generated on this date for this engagement slice.")
    engagement_id = serializers.IntegerField(help_text="Engagement primary key.")
    person_id = serializers.CharField(allow_null=True, help_text="Person primary key.")
    person_name = serializers.CharField(allow_null=True, help_text="Person display name; may be null if inaccessible.")
    order_id = serializers.IntegerField(allow_null=True, help_text="Order primary key; null on inactive days.")
    order_name = serializers.CharField(allow_null=True, help_text="Order display name; may be null.")
    company_id = serializers.IntegerField(allow_null=True, help_text="Company primary key; null on inactive days.")
    company_name = serializers.CharField(allow_null=True, help_text="Company display name; may be null.")
    undertaking_id = serializers.IntegerField(
        allow_null=True,
        help_text="Undertaking primary key; null when the day is under-covered by undertaking assignments.",
    )
    undertaking_name = serializers.CharField(allow_null=True, help_text="Undertaking display name; may be null.")
    percentage = serializers.FloatField(help_text="Share of the day attributed to this undertaking (0.0-1.0).")
    daily_rate = serializers.FloatField(help_text="Engagement daily rate before any adjustment.")
    fte = serializers.FloatField(help_text="Engagement FTE (0.0-1.0).")
    is_working_day = serializers.BooleanField(help_text="False when a calendar assignment marks the day non-working.")


class _CostLinesResponseSerializer(serializers.Serializer[Any]):
    """The full cost-lines response payload."""

    date_from = serializers.CharField(help_text="Echo of the request date_from (YYYY-MM-DD).")
    date_to = serializers.CharField(help_text="Echo of the request date_to (YYYY-MM-DD).")
    count = serializers.IntegerField(help_text="Number of rows in the response.")
    rows = _CostLineRowSerializer(many=True, help_text="Unaggregated day-level cost rows.")


_COST_LINES_DESCRIPTION = (
    "Returns unaggregated day-level cost rows with denormalized display names "
    "for every dimension (person, order, company, undertaking). All results are "
    "scoped to entities accessible to the requesting user (FR-45). The GET "
    "variant accepts filter parameters in the query string; POST accepts them "
    "as JSON. ``date_from`` and ``date_to`` are required; the span is capped "
    "at ``settings.DASHBOARDS_COST_LINES_MAX_DAYS`` (default 400 days) and a "
    "wider request returns HTTP 400."
)

_COST_LINES_EXAMPLES = [
    OpenApiExample(
        "One-month reconciliation for a company",
        value={
            "date_from": "2026-07-01",
            "date_to": "2026-07-31",
            "company_ids": [9],
            "person_ids": [],
            "order_ids": [],
            "undertaking_ids": [],
            "engagement_ids": [],
        },
        request_only=True,
    ),
]


@extend_schema(
    summary="Dashboard cost lines (GET)",
    description=_COST_LINES_DESCRIPTION,
    parameters=[_CostLinesRequestSerializer],
    responses={200: _CostLinesResponseSerializer},
    examples=_COST_LINES_EXAMPLES,
    tags=["dashboards"],
)
class DashboardCostLinesView(APIView):
    """GET/POST ``/api/v1/dashboards/cost-lines/``.

    Both verbs delegate to :func:`dashboards.services.build_cost_lines` after
    validating the filter parameters. The permission classes are inherited
    from :class:`DashboardSummaryView` so behaviour matches the summary
    endpoint exactly (FR-22, FR-45).
    """

    permission_classes = DashboardSummaryView.permission_classes

    def _run(self, data: Any) -> Response:
        """Validate *data*, call the service, and return the HTTP response.

        Args:
            data: Raw input dict (from query params or request body).

        Returns:
            200 response with the serialised :data:`CostLinesPayload`.
            400 when input validation fails or the date span exceeds the cap.
        """
        req_ser = _CostLinesRequestSerializer(data=data)
        if not req_ser.is_valid():
            return Response(req_ser.errors, status=400)

        params = req_ser.validated_data
        try:
            payload = build_cost_lines(
                user=cast(User, self.request.user),
                date_range=(params["date_from"], params["date_to"]),
                entity_selection=_entity_selection_from_params(params),
            )
        except CostLinesSpanTooLargeError as exc:
            return Response({"detail": str(exc)}, status=400)

        resp_ser = _CostLinesResponseSerializer(payload)
        return Response(resp_ser.data)

    def get(self, request: Request) -> Response:
        """Handle ``GET /api/v1/dashboards/cost-lines/``.

        Args:
            request: The incoming DRF request. Filter parameters are read
                from the query string.

        Returns:
            200 with the cost-lines payload, or 400 on validation failure.
        """
        return self._run(request.query_params)

    @extend_schema(
        summary="Dashboard cost lines (POST)",
        description=_COST_LINES_DESCRIPTION,
        request=_CostLinesRequestSerializer,
        responses={200: _CostLinesResponseSerializer},
        examples=_COST_LINES_EXAMPLES,
        tags=["dashboards"],
    )
    def post(self, request: Request) -> Response:
        """Handle ``POST /api/v1/dashboards/cost-lines/``.

        Args:
            request: The incoming DRF request. Filter parameters are read
                from the JSON request body.

        Returns:
            200 with the cost-lines payload, or 400 on validation failure.
        """
        return self._run(dict(request.data))
