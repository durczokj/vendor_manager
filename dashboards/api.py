"""API view for the dashboards app.

Exposes ``GET /api/v1/dashboards/summary/`` and
``POST /api/v1/dashboards/summary/`` which both delegate to
:func:`dashboards.services.build_summary`.

Also exposes ``GET /api/v1/dashboards/entity-options/`` which returns the
lists of entities accessible to the requesting user, used to populate the
dashboard filter dropdowns (FR-43, FR-46).
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
from dashboards.services import VALID_CLASSES, VALID_GRANULARITIES, build_summary
from engagements.models import Engagement
from orders.models import Order
from people.models import Person
from undertakings.models import Undertaking


class _SummaryRequestSerializer(serializers.Serializer[Any]):
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
    # Entity-specific selection filters.
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
