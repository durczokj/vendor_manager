"""FilterSets for the companies app."""

from django_filters import rest_framework as filters

from companies.models import Company


class CompanyFilterSet(filters.FilterSet):  # type: ignore[misc]  # TODO(P8): add django-filter stubs
    """FilterSet for the Company model."""

    class Meta:
        """FilterSet metadata."""

        model = Company
        fields = ["name"]
