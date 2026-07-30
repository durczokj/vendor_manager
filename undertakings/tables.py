"""django-tables2 table classes for the undertakings app."""

import django_tables2 as tables

from vendor_manager.tables import BaseEntityTable

from .models import Undertaking

_UNDERTAKING_ACTIONS = """
{% if table.can_manage %}
<a href="{% url 'undertaking-update' record.pk %}" class="inline"><button>Edit</button></a>
<a href="{% url 'undertaking-delete' record.pk %}" class="inline"><button>Delete</button></a>
{% endif %}
"""


class UndertakingTable(BaseEntityTable):
    """Table for listing Undertaking records."""

    id = tables.Column(linkify=("undertaking-detail", {"pk": tables.A("pk")}))
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
