"""ViewSet for the people app."""

from typing import Any

from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from engagements.models import EngagementUndertakingAssignment
from engagements.serializers import EngagementUndertakingAssignmentSerializer
from people.filters import PersonFilterSet
from people.managers import PersonQuerySet
from people.models import Person
from people.serializers import PersonSerializer


class PersonViewSet(viewsets.ModelViewSet[Person]):
    """Person list/create/retrieve/update/destroy endpoints."""

    queryset = Person.objects.all().order_by("id")
    serializer_class = PersonSerializer
    filterset_class = PersonFilterSet
    search_fields = ["first_name", "last_name", "location"]
    ordering_fields = ["id", "first_name", "last_name"]

    def get_queryset(self) -> PersonQuerySet:
        """Return people accessible to the requesting user."""
        assert self.request.user.is_authenticated
        return Person.objects.accessible_to(self.request.user).order_by("id")

    @extend_schema(
        responses={200: EngagementUndertakingAssignmentSerializer(many=True)},
        summary="List undertaking assignments for a person",
        description=(
            "Returns all EngagementUndertakingAssignment records that belong to the given person "
            "and are accessible to the requesting user."
        ),
    )
    @action(detail=True, methods=["get"], url_path="assignments")
    def assignments(self, request: Request, pk: Any = None) -> Response:
        """Return undertaking assignments for this person (FR-31).

        Args:
            request: The incoming DRF request.
            pk: The primary key of the Person.

        Returns:
            200 with a list of EngagementUndertakingAssignment records.

        """
        assert request.user.is_authenticated
        person: Person = self.get_object()
        qs = (
            EngagementUndertakingAssignment.objects.accessible_to(request.user)
            .filter(engagement__person=person)
            .order_by("id")
        )
        serializer = EngagementUndertakingAssignmentSerializer(qs, many=True)
        return Response(serializer.data)
