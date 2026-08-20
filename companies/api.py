"""ViewSet for the companies app."""

from rest_framework import viewsets

from companies.filters import CompanyFilterSet
from companies.managers import CompanyQuerySet
from companies.models import Company
from companies.serializers import CompanySerializer


class CompanyViewSet(viewsets.ModelViewSet[Company]):
    """Company list/create/retrieve/update/destroy endpoints."""

    queryset = Company.objects.all().order_by("id")
    serializer_class = CompanySerializer
    filterset_class = CompanyFilterSet
    search_fields = ["name", "email"]
    ordering_fields = ["id", "name"]

    def get_queryset(self) -> CompanyQuerySet:
        """Return companies accessible to the requesting user."""
        assert self.request.user.is_authenticated
        return Company.objects.accessible_to(self.request.user).order_by("id")
