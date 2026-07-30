"""django-tables2 table classes for the companies app."""

import django_tables2 as tables

from vendor_manager.tables import BaseEntityTable

from .models import Company

_COMPANY_ACTIONS = """
{% if table.can_manage %}
<a href="{% url 'company-update' record.pk %}" class="inline"><button>Edit</button></a>
<a href="{% url 'company-delete' record.pk %}" class="inline"><button>Delete</button></a>
{% endif %}
"""


class CompanyTable(BaseEntityTable):
    """Table for listing Company records."""

    id = tables.Column(linkify=("company-detail", {"pk": tables.A("pk")}))
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
