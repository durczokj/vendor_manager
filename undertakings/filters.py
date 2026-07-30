"""FilterSets for the undertakings app."""

from django_filters import rest_framework as filters

from undertakings.models import CostCenter, Undertaking


class CostCenterFilterSet(filters.FilterSet):  # type: ignore[misc]  # TODO(P8): add django-filter stubs
    """FilterSet for the CostCenter model."""

    class Meta:
        """FilterSet metadata."""

        model = CostCenter
        fields = ["name"]


class UndertakingFilterSet(filters.FilterSet):  # type: ignore[misc]  # TODO(P8): add django-filter stubs
    """FilterSet for the Undertaking model."""

    class Meta:
        """FilterSet metadata."""

        model = Undertaking
        fields = ["name", "cost_center", "manager"]
