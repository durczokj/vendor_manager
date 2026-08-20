"""FilterSets for the contracts app."""

from django_filters import rest_framework as filters

from contracts.models import Contract


class ContractFilterSet(filters.FilterSet):
    """FilterSet for the Contract model."""

    class Meta:
        """FilterSet metadata."""

        model = Contract
        fields = ["name", "status"]
