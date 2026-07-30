"""django-tables2 table classes for the contracts app."""

import django_tables2 as tables

from vendor_manager.tables import BaseEntityTable

from .models import Contract

_CONTRACT_ACTIONS = """
{% if table.can_manage %}
{% url 'contract' 0 as delete_pattern %}
{% url 'contract' record.pk as edit_url %}
<form onsubmit="deleteResource(event,'{{ delete_pattern }}','{{ record.pk }}','{{ csrf_token }}');" class="inline">
  <button type="submit" onclick="return confirm('Delete this contract?');">Delete</button>
</form>
<a href="{{ edit_url }}?form=True" class="inline"><button>Edit</button></a>
{% endif %}
"""


class ContractTable(BaseEntityTable):
    """Table for listing Contract records."""

    id = tables.Column(linkify=("contract", {"item_id": tables.A("pk")}))
    actions = tables.TemplateColumn(
        template_code=_CONTRACT_ACTIONS,
        orderable=False,
        verbose_name="Actions",
    )

    class Meta:
        """Table meta options."""

        model = Contract
        fields = ("id", "name", "status", "size", "actions")
        attrs = {"class": "table table-striped table-hover"}
