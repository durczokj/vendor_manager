"""Serializers for the undertakings app."""

from rest_framework import serializers

from undertakings.models import CostCenter, Undertaking
from vendor_manager.api_serializers import ImmutablePkSerializerMixin


class CostCenterSerializer(ImmutablePkSerializerMixin, serializers.ModelSerializer[CostCenter]):
    """Serialize CostCenter rows for API operations."""

    class Meta:
        """Model serializer metadata."""

        model = CostCenter
        fields = ["id", "name"]


class UndertakingSerializer(ImmutablePkSerializerMixin, serializers.ModelSerializer[Undertaking]):
    """Serialize Undertaking rows for API operations."""

    class Meta:
        """Model serializer metadata."""

        model = Undertaking
        fields = ["id", "name", "cost_center", "manager"]
