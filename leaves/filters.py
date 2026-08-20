"""FilterSets for the leaves app."""

from django_filters import rest_framework as filters

from leaves.models import Leave


class LeaveFilterSet(filters.FilterSet):
    """FilterSet for the Leave model."""

    class Meta:
        """FilterSet metadata."""

        model = Leave
        fields = ["person"]
