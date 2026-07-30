"""django-tables2 table classes for the undertakings app."""

import django_tables2 as tables

from vendor_manager.tables import BaseEntityTable

from .models import Undertaking

_UNDERTAKING_ACTIONS = """
{% if table.can_manage %}
{% url 'undertaking' 0 as delete_pattern %}
{% url 'undertaking' record.pk as edit_url %}
<form onsubmit="deleteResource(event,'{{ delete_pattern }}','{{ record.pk }}','{{ csrf_token }}');" class="inline">
  <button type="submit" onclick="return confirm('Delete this undertaking?');">Delete</button>
</form>
<a href="{{ edit_url }}?form=True" class="inline"><button>Edit</button></a>
{% endif %}
"""


class UndertakingTable(BaseEntityTable):
    """Table for listing Undertaking records."""

    id = tables.Column(linkify=("undertaking", {"item_id": tables.A("pk")}))
    actions = tables.TemplateColumn(
        template_code=_UNDERTAKING_ACTIONS,
        orderable=False,
        verbose_name="Actions",
    )

    class Meta:
        """Table meta options."""

        model = Undertaking
        fields = ("id", "name", "cost_center", "manager", "actions")
        attrs = {"class": "table table-striped table-hover"}
