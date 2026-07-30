"""Serializers for the leaves app."""

from decimal import Decimal

from rest_framework import serializers

from leaves.models import Leave


class LeaveSerializer(serializers.ModelSerializer[Leave]):
    """Serialize Leave rows for API operations."""

    # Override to provide Decimal min/max values (the model validators use int
    # literals which would trigger a UserWarning in DRF schema generation).
    percentage = serializers.DecimalField(
        max_digits=3,
        decimal_places=2,
        min_value=Decimal("0"),
        max_value=Decimal("1"),
    )

    class Meta:
        """Model serializer metadata."""

        model = Leave
        fields = ["id", "person", "start_date", "end_date", "percentage"]
