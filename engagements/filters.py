"""FilterSets for the engagements app."""

from django_filters import rest_framework as filters

from engagements.models import Engagement, EngagementOrderVersionAssignment, EngagementUndertakingAssignment


class EngagementFilterSet(filters.FilterSet):
    """FilterSet for the Engagement model."""

    class Meta:
        """FilterSet metadata."""

        model = Engagement
        fields = ["person"]


class EngagementOrderVersionAssignmentFilterSet(filters.FilterSet):
    """FilterSet for the EngagementOrderVersionAssignment model."""

    class Meta:
        """FilterSet metadata."""

        model = EngagementOrderVersionAssignment
        fields = ["engagement", "order_version"]


class EngagementUndertakingAssignmentFilterSet(filters.FilterSet):
    """FilterSet for the EngagementUndertakingAssignment model."""

    class Meta:
        """FilterSet metadata."""

        model = EngagementUndertakingAssignment
        fields = ["engagement", "undertaking"]
