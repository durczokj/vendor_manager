"""ViewSet for the leaves app."""

from rest_framework import viewsets

from leaves.filters import LeaveFilterSet
from leaves.managers import LeaveQuerySet
from leaves.models import Leave
from leaves.serializers import LeaveSerializer


class LeaveViewSet(viewsets.ModelViewSet[Leave]):
    """Leave list/create/retrieve/update/destroy endpoints."""

    queryset = Leave.objects.all().order_by("id")
    serializer_class = LeaveSerializer
    filterset_class = LeaveFilterSet
    search_fields: list[str] = []
    ordering_fields = ["id", "start_date", "end_date", "percentage"]

    def get_queryset(self) -> LeaveQuerySet:
        """Return leaves accessible to the requesting user."""
        assert self.request.user.is_authenticated
        return Leave.objects.accessible_to(self.request.user).order_by("id")
