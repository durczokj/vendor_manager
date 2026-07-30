"""django-tables2 table classes for the people app."""

import django_tables2 as tables

from vendor_manager.tables import BaseEntityTable

from .models import Person

_PERSON_ACTIONS = """
{% if table.can_manage %}
<a href="{% url 'person-update' record.pk %}" class="inline"><button>Edit</button></a>
<a href="{% url 'person-delete' record.pk %}" class="inline"><button>Delete</button></a>
{% endif %}
"""


class PersonTable(BaseEntityTable):
    """Table for listing Person records."""

    id = tables.Column(linkify=("person-detail", {"pk": tables.A("pk")}))
    actions = tables.TemplateColumn(
        template_code=_PERSON_ACTIONS,
        orderable=False,
        verbose_name="Actions",
    )

    class Meta:
        """Table meta options."""

        model = Person
        fields = ("id", "first_name", "last_name", "description", "location", "actions")
        attrs = {"class": "table table-striped table-hover"}
