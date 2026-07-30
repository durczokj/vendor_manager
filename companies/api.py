"""ViewSet for the companies app."""

from typing import Any

from rest_framework import viewsets

from companies.filters import CompanyFilterSet
from companies.models import Company
from companies.serializers import CompanySerializer


class CompanyViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]  # TODO(P8): add type param
    """Company list/create/retrieve/update/destroy endpoints."""

    queryset = Company.objects.all().order_by("id")
    serializer_class = CompanySerializer
    filterset_class = CompanyFilterSet
    search_fields = ["name", "email"]
    ordering_fields = ["id", "name"]

    def get_queryset(self) -> Any:
        """Return companies accessible to the requesting user."""
        return super().get_queryset().accessible_to(self.request.user)  # type: ignore[attr-defined]
