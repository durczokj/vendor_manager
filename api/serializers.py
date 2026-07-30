"""Serializers used by the API surface."""

from rest_framework import serializers

from companies.models import Company


class CompanySerializer(serializers.ModelSerializer[Company]):
    """Serialize company rows for API create/list operations."""

    class Meta:
        """Model serializer metadata."""

        model = Company
        fields = ["id", "name", "email"]
