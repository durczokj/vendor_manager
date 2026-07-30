"""django-tables2 table classes for the orders app."""

import django_tables2 as tables

from vendor_manager.tables import BaseEntityTable

from .models import Order, OrderVersion

_ORDER_ACTIONS = """
{% if table.can_manage %}
{% url 'order' 0 as delete_pattern %}
{% url 'order' record.pk as edit_url %}
<form onsubmit="deleteResource(event, '{{ delete_pattern }}', '{{ record.pk }}', '{{ csrf_token }}');" class="inline">
  <button type="submit" onclick="return confirm('Delete this order?');">Delete</button>
</form>
<a href="{{ edit_url }}?form=True" class="inline"><button>Edit</button></a>
{% endif %}
"""

_ORDER_VERSION_ACTIONS = """
{% if table.can_manage %}
{% url 'order_version' 0 as delete_pattern %}
{% url 'order_version' record.pk as edit_url %}
<form onsubmit="deleteResource(event, '{{ delete_pattern }}', '{{ record.pk }}', '{{ csrf_token }}');" class="inline">
  <button type="submit" onclick="return confirm('Delete this order version?');">Delete</button>
</form>
<a href="{{ edit_url }}?form=True" class="inline"><button>Edit</button></a>
{% endif %}
"""


class OrderTable(BaseEntityTable):
    """Table for listing Order records."""

    id = tables.Column(linkify=("order", {"item_id": tables.A("pk")}))
    actions = tables.TemplateColumn(
        template_code=_ORDER_ACTIONS,
        orderable=False,
        verbose_name="Actions",
    )

    class Meta:
        """Table meta options."""

        model = Order
        fields = ("id", "name", "company", "actions")
        attrs = {"class": "table table-striped table-hover"}


class OrderVersionTable(BaseEntityTable):
    """Table for listing OrderVersion records."""

    id = tables.Column(linkify=("order_version", {"item_id": tables.A("pk")}))
    start_date = tables.DateColumn(format="Y-m-d")
    end_date = tables.DateColumn(format="Y-m-d")
    actions = tables.TemplateColumn(
        template_code=_ORDER_VERSION_ACTIONS,
        orderable=False,
        verbose_name="Actions",
    )

    class Meta:
        """Table meta options."""

        model = OrderVersion
        fields = ("id", "order", "version_number", "contract", "start_date", "end_date", "actions")
        attrs = {"class": "table table-striped table-hover"}
