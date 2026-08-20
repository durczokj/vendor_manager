"""FilterSets for the orders app."""

from django_filters import rest_framework as filters

from orders.models import Order, OrderVersion


class OrderFilterSet(filters.FilterSet):
    """FilterSet for the Order model."""

    class Meta:
        """FilterSet metadata."""

        model = Order
        fields = ["name", "company"]


class OrderVersionFilterSet(filters.FilterSet):
    """FilterSet for the OrderVersion model."""

    class Meta:
        """FilterSet metadata."""

        model = OrderVersion
        fields = ["order", "contract", "version_number"]
