"""Serializers for the people app."""

from rest_framework import serializers

from people.models import Person
from vendor_manager.api_serializers import ImmutablePkSerializerMixin


class PersonSerializer(ImmutablePkSerializerMixin, serializers.ModelSerializer[Person]):
    """Serialize Person rows for API operations."""

    class Meta:
        """Model serializer metadata."""

        model = Person
        fields = ["id", "first_name", "last_name", "description", "location", "user"]
