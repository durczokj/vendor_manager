"""FilterSets for the orders app."""

from django_filters import rest_framework as filters

from orders.models import Order, OrderVersion


class OrderFilterSet(filters.FilterSet):  # type: ignore[misc]  # TODO(P8): add django-filter stubs
    """FilterSet for the Order model."""

    class Meta:
        """FilterSet metadata."""

        model = Order
        fields = ["name", "company"]


class OrderVersionFilterSet(filters.FilterSet):  # type: ignore[misc]  # TODO(P8): add django-filter stubs
    """FilterSet for the OrderVersion model."""

    class Meta:
        """FilterSet metadata."""

        model = OrderVersion
        fields = ["order", "contract", "version_number"]
