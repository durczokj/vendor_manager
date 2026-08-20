"""FilterSets for the people app."""

from django_filters import rest_framework as filters

from people.models import Person


class PersonFilterSet(filters.FilterSet):
    """FilterSet for the Person model."""

    class Meta:
        """FilterSet metadata."""

        model = Person
        fields = ["first_name", "last_name", "location"]
