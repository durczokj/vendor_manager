"""ViewSet for the contracts app."""

from typing import Any

from rest_framework import viewsets

from contracts.filters import ContractFilterSet
from contracts.models import Contract
from contracts.serializers import ContractSerializer


class ContractViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]  # TODO(P8): add type param
    """Contract list/create/retrieve/update/destroy endpoints."""

    queryset = Contract.objects.all().order_by("id")
    serializer_class = ContractSerializer
    filterset_class = ContractFilterSet
    search_fields = ["name", "status"]
    ordering_fields = ["id", "name", "status", "size"]

    def get_queryset(self) -> Any:
        """Return contracts accessible to the requesting user."""
        return super().get_queryset().accessible_to(self.request.user)  # type: ignore[attr-defined]
