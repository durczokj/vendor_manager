"""ViewSet for the people app."""

from typing import Any

from rest_framework import viewsets

from people.filters import PersonFilterSet
from people.models import Person
from people.serializers import PersonSerializer


class PersonViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]  # TODO(P8): add type param
    """Person list/create/retrieve/update/destroy endpoints."""

    queryset = Person.objects.all().order_by("id")
    serializer_class = PersonSerializer
    filterset_class = PersonFilterSet
    search_fields = ["first_name", "last_name", "location"]
    ordering_fields = ["id", "first_name", "last_name"]

    def get_queryset(self) -> Any:
        """Return people accessible to the requesting user."""
        return super().get_queryset().accessible_to(self.request.user)  # type: ignore[attr-defined]
