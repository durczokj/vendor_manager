"""django-tables2 table classes for the contracts app."""

import django_tables2 as tables

from vendor_manager.tables import BaseEntityTable

from .models import Contract

_CONTRACT_ACTIONS = """
{% if table.can_manage %}
<a href="{% url 'contract-update' record.pk %}" class="inline"><button>Edit</button></a>
<a href="{% url 'contract-delete' record.pk %}" class="inline"><button>Delete</button></a>
{% endif %}
"""


class ContractTable(BaseEntityTable):
    """Table for listing Contract records."""

    id = tables.Column(linkify=("contract-detail", {"pk": tables.A("pk")}))
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
