"""FilterSets for the engagements app."""

from django_filters import rest_framework as filters

from engagements.models import Engagement, EngagementOrderVersionAssignment, EngagementUndertakingAssignment


class EngagementFilterSet(filters.FilterSet):  # type: ignore[misc]  # TODO(P8): add django-filter stubs
    """FilterSet for the Engagement model."""

    class Meta:
        """FilterSet metadata."""

        model = Engagement
        fields = ["person"]


class EngagementOrderVersionAssignmentFilterSet(filters.FilterSet):  # type: ignore[misc]  # TODO(P8): add django-filter stubs
    """FilterSet for the EngagementOrderVersionAssignment model."""

    class Meta:
        """FilterSet metadata."""

        model = EngagementOrderVersionAssignment
        fields = ["engagement", "order_version"]


class EngagementUndertakingAssignmentFilterSet(filters.FilterSet):  # type: ignore[misc]  # TODO(P8): add django-filter stubs
    """FilterSet for the EngagementUndertakingAssignment model."""

    class Meta:
        """FilterSet metadata."""

        model = EngagementUndertakingAssignment
        fields = ["engagement", "undertaking"]
