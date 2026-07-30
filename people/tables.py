"""django-tables2 table classes for the people app."""

import django_tables2 as tables

from vendor_manager.tables import BaseEntityTable

from .models import Person

_PERSON_ACTIONS = """
{% if table.can_manage %}
{% url 'person' 0 as delete_pattern %}
{% url 'person' record.pk as edit_url %}
<form onsubmit="deleteResource(event,'{{ delete_pattern }}','{{ record.pk }}','{{ csrf_token }}');" class="inline">
  <button type="submit" onclick="return confirm('Delete this person?');">Delete</button>
</form>
<a href="{{ edit_url }}?form=True" class="inline"><button>Edit</button></a>
{% endif %}
"""


class PersonTable(BaseEntityTable):
    """Table for listing Person records."""

    id = tables.Column(linkify=("person", {"item_id": tables.A("pk")}))
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
