"""ViewSets for the orders app."""

from typing import Any

from drf_spectacular.utils import extend_schema
from rest_framework import serializers as drf_serializers
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from contracts.models import Contract
from orders.filters import OrderFilterSet, OrderVersionFilterSet
from orders.models import Order, OrderVersion
from orders.serializers import OrderSerializer, OrderVersionSerializer
from orders.services import create_new_order_version


class CloneLatestVersionSerializer(drf_serializers.Serializer[Any]):
    """Request body for the clone-latest action."""

    contract_id = drf_serializers.IntegerField()
    start_date = drf_serializers.DateField()
    end_date = drf_serializers.DateField()
    copy_engagement_assignments = drf_serializers.BooleanField(default=True)


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

    @extend_schema(
        request=CloneLatestVersionSerializer,
        responses={201: OrderVersionSerializer},
        summary="Clone the latest version of an order",
        description=(
            "Creates a new OrderVersion by cloning the latest version of the given order. "
            "Optionally copies existing engagement assignments. "
            "Requires the requesting user to have access to the order."
        ),
    )
    @action(detail=True, methods=["post"], url_path="versions/clone-latest")
    def clone_latest_version(self, request: Request, pk: Any = None) -> Response:
        """Clone the latest order version (FR-31).

        Args:
            request: The incoming DRF request.
            pk: The primary key of the Order.

        Returns:
            201 with the new OrderVersion, or 403/404 if inaccessible.

        Raises:
            PermissionDenied: When the user cannot access the order.

        """
        order: Order = self.get_object()

        # get_object() already calls check_object_permissions, which uses
        # get_queryset() filtered by accessible_to(user) — so a user who lacks
        # access to this order receives a 404 before we reach this point.

        serializer = CloneLatestVersionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        contract = drf_serializers.PrimaryKeyRelatedField(queryset=Contract.objects.all()).to_internal_value(
            data["contract_id"]
        )

        new_version = create_new_order_version(
            order=order,
            contract=contract,
            start_date=data["start_date"],
            end_date=data["end_date"],
            copy_engagement_assignments=data["copy_engagement_assignments"],
        )
        out = OrderVersionSerializer(new_version)
        return Response(out.data, status=status.HTTP_201_CREATED)


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
