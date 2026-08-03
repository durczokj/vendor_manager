"""Serializers for the companies app."""

from rest_framework import serializers

from companies.models import Company
from vendor_manager.api_serializers import ImmutablePkSerializerMixin


class CompanySerializer(ImmutablePkSerializerMixin, serializers.ModelSerializer[Company]):
    """Serialize Company rows for API operations."""

    class Meta:
        """Model serializer metadata."""

        model = Company
        fields = ["id", "name", "email"]
