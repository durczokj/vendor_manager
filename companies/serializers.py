"""Serializers for the companies app."""

from rest_framework import serializers

from companies.models import Company


class CompanySerializer(serializers.ModelSerializer[Company]):
    """Serialize Company rows for API operations."""

    class Meta:
        """Model serializer metadata."""

        model = Company
        fields = ["id", "name", "email"]
