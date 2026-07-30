"""ViewSets for the orders app."""

from typing import Any

from rest_framework import viewsets

from orders.filters import OrderFilterSet, OrderVersionFilterSet
from orders.models import Order, OrderVersion
from orders.serializers import OrderSerializer, OrderVersionSerializer


class OrderViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]  # TODO(P8): add type param
    """Order list/create/retrieve/update/destroy endpoints."""

    queryset = Order.objects.all().order_by("id")
    serializer_class = OrderSerializer
    filterset_class = OrderFilterSet
    search_fields = ["name"]
    ordering_fields = ["id", "name"]

    def get_queryset(self) -> Any:
        """Return orders accessible to the requesting user."""
        return super().get_queryset().accessible_to(self.request.user)  # type: ignore[attr-defined]


class OrderVersionViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]  # TODO(P8): add type param
    """OrderVersion list/create/retrieve/update/destroy endpoints."""

    queryset = OrderVersion.objects.all().order_by("id")
    serializer_class = OrderVersionSerializer
    filterset_class = OrderVersionFilterSet
    search_fields: list[str] = []
    ordering_fields = ["id", "version_number", "start_date", "end_date"]

    def get_queryset(self) -> Any:
        """Return order versions accessible to the requesting user."""
        return super().get_queryset().accessible_to(self.request.user)  # type: ignore[attr-defined]
