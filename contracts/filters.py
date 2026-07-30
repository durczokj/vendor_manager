"""FilterSets for the contracts app."""

from django_filters import rest_framework as filters

from contracts.models import Contract


class ContractFilterSet(filters.FilterSet):  # type: ignore[misc]  # TODO(P8): add django-filter stubs
    """FilterSet for the Contract model."""

    class Meta:
        """FilterSet metadata."""

        model = Contract
        fields = ["name", "status"]
