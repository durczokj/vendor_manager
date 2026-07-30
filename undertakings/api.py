"""ViewSets for the undertakings app."""

from typing import Any

from rest_framework import viewsets

from undertakings.filters import CostCenterFilterSet, UndertakingFilterSet
from undertakings.models import CostCenter, Undertaking
from undertakings.serializers import CostCenterSerializer, UndertakingSerializer


class CostCenterViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]  # TODO(P8): add type param
    """CostCenter list/create/retrieve/update/destroy endpoints."""

    queryset = CostCenter.objects.all().order_by("id")
    serializer_class = CostCenterSerializer
    filterset_class = CostCenterFilterSet
    search_fields = ["name"]
    ordering_fields = ["id", "name"]

    def get_queryset(self) -> Any:
        """Return cost centers accessible to the requesting user."""
        return super().get_queryset().accessible_to(self.request.user)  # type: ignore[attr-defined]


class UndertakingViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]  # TODO(P8): add type param
    """Undertaking list/create/retrieve/update/destroy endpoints."""

    queryset = Undertaking.objects.all().order_by("id")
    serializer_class = UndertakingSerializer
    filterset_class = UndertakingFilterSet
    search_fields = ["name"]
    ordering_fields = ["id", "name"]

    def get_queryset(self) -> Any:
        """Return undertakings accessible to the requesting user."""
        return super().get_queryset().accessible_to(self.request.user)  # type: ignore[attr-defined]
