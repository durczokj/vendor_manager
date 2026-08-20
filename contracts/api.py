"""ViewSet for the contracts app."""

from rest_framework import viewsets

from contracts.filters import ContractFilterSet
from contracts.managers import ContractQuerySet
from contracts.models import Contract
from contracts.serializers import ContractSerializer


class ContractViewSet(viewsets.ModelViewSet[Contract]):
    """Contract list/create/retrieve/update/destroy endpoints."""

    queryset = Contract.objects.all().order_by("id")
    serializer_class = ContractSerializer
    filterset_class = ContractFilterSet
    search_fields = ["name", "status"]
    ordering_fields = ["id", "name", "status", "size"]

    def get_queryset(self) -> ContractQuerySet:
        """Return contracts accessible to the requesting user."""
        assert self.request.user.is_authenticated
        return Contract.objects.accessible_to(self.request.user).order_by("id")
