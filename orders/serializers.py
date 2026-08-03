"""Serializers for the orders app."""

from rest_framework import serializers

from orders.models import Order, OrderVersion
from vendor_manager.api_serializers import ImmutablePkSerializerMixin


class OrderSerializer(ImmutablePkSerializerMixin, serializers.ModelSerializer[Order]):
    """Serialize Order rows for API operations."""

    class Meta:
        """Model serializer metadata."""

        model = Order
        fields = ["id", "name", "company"]


class OrderVersionSerializer(serializers.ModelSerializer[OrderVersion]):
    """Serialize OrderVersion rows for API operations."""

    class Meta:
        """Model serializer metadata."""

        model = OrderVersion
        fields = ["id", "order", "contract", "version_number", "start_date", "end_date"]
