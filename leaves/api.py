"""ViewSet for the leaves app."""

from typing import Any

from rest_framework import viewsets

from leaves.filters import LeaveFilterSet
from leaves.models import Leave
from leaves.serializers import LeaveSerializer


class LeaveViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]  # TODO(P8): add type param
    """Leave list/create/retrieve/update/destroy endpoints."""

    queryset = Leave.objects.all().order_by("id")
    serializer_class = LeaveSerializer
    filterset_class = LeaveFilterSet
    search_fields: list[str] = []
    ordering_fields = ["id", "start_date", "end_date", "percentage"]

    def get_queryset(self) -> Any:
        """Return leaves accessible to the requesting user."""
        return super().get_queryset().accessible_to(self.request.user)  # type: ignore[attr-defined]
