"""Serializers for the engagements app."""

from rest_framework import serializers

from engagements.models import Engagement, EngagementOrderVersionAssignment, EngagementUndertakingAssignment


class EngagementSerializer(serializers.ModelSerializer[Engagement]):
    """Serialize Engagement rows for API operations."""

    class Meta:
        """Model serializer metadata."""

        model = Engagement
        fields = ["id", "person", "start_date", "end_date", "daily_rate", "fte"]


class EngagementOrderVersionAssignmentSerializer(serializers.ModelSerializer[EngagementOrderVersionAssignment]):
    """Serialize EngagementOrderVersionAssignment rows for API operations."""

    class Meta:
        """Model serializer metadata."""

        model = EngagementOrderVersionAssignment
        fields = ["id", "engagement", "order_version"]


class EngagementUndertakingAssignmentSerializer(serializers.ModelSerializer[EngagementUndertakingAssignment]):
    """Serialize EngagementUndertakingAssignment rows for API operations."""

    class Meta:
        """Model serializer metadata."""

        model = EngagementUndertakingAssignment
        fields = ["id", "engagement", "undertaking", "start_date", "end_date", "percentage"]
