"""ViewSets for the undertakings app."""

from rest_framework import viewsets

from undertakings.filters import CostCenterFilterSet, UndertakingFilterSet
from undertakings.managers import CostCenterQuerySet, UndertakingQuerySet
from undertakings.models import CostCenter, Undertaking
from undertakings.serializers import CostCenterSerializer, UndertakingSerializer


class CostCenterViewSet(viewsets.ModelViewSet[CostCenter]):
    """CostCenter list/create/retrieve/update/destroy endpoints."""

    queryset = CostCenter.objects.all().order_by("id")
    serializer_class = CostCenterSerializer
    filterset_class = CostCenterFilterSet
    search_fields = ["name"]
    ordering_fields = ["id", "name"]

    def get_queryset(self) -> CostCenterQuerySet:
        """Return cost centers accessible to the requesting user."""
        assert self.request.user.is_authenticated
        return CostCenter.objects.accessible_to(self.request.user).order_by("id")


class UndertakingViewSet(viewsets.ModelViewSet[Undertaking]):
    """Undertaking list/create/retrieve/update/destroy endpoints."""

    queryset = Undertaking.objects.all().order_by("id")
    serializer_class = UndertakingSerializer
    filterset_class = UndertakingFilterSet
    search_fields = ["name"]
    ordering_fields = ["id", "name"]

    def get_queryset(self) -> UndertakingQuerySet:
        """Return undertakings accessible to the requesting user."""
        assert self.request.user.is_authenticated
        return Undertaking.objects.accessible_to(self.request.user).order_by("id")
