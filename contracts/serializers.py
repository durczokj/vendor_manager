"""Serializers for the contracts app."""

from rest_framework import serializers

from contracts.models import Contract


class ContractSerializer(serializers.ModelSerializer[Contract]):
    """Serialize Contract rows for API operations."""

    class Meta:
        """Model serializer metadata."""

        model = Contract
        fields = ["id", "name", "status", "size"]
