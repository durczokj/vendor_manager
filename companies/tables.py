"""django-tables2 table classes for the companies app."""

import django_tables2 as tables

from vendor_manager.tables import BaseEntityTable

from .models import Company

_COMPANY_ACTIONS = """
{% if table.can_manage %}
{% url 'company' 0 as delete_pattern %}
{% url 'company' record.pk as edit_url %}
<form onsubmit="deleteResource(event,'{{ delete_pattern }}','{{ record.pk }}','{{ csrf_token }}');" class="inline">
  <button type="submit" onclick="return confirm('Delete this company?');">Delete</button>
</form>
<a href="{{ edit_url }}?form=True" class="inline"><button>Edit</button></a>
{% endif %}
"""


class CompanyTable(BaseEntityTable):
    """Table for listing Company records."""

    id = tables.Column(linkify=("company", {"item_id": tables.A("pk")}))
    actions = tables.TemplateColumn(
        template_code=_COMPANY_ACTIONS,
        orderable=False,
        verbose_name="Actions",
    )

    class Meta:
        """Table meta options."""

        model = Company
        fields = ("id", "name", "email", "actions")
        attrs = {"class": "table table-striped table-hover"}
