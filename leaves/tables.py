"""django-tables2 table classes for the leaves app."""

import django_tables2 as tables

from vendor_manager.tables import BaseEntityTable

from .models import Leave

_LEAVE_ACTIONS = """
<a href="{% url 'leave-delete' record.pk %}"><button>Delete</button></a>
"""


class LeaveTable(BaseEntityTable):
    """Table for listing Leave records."""

    start_date = tables.DateColumn(format="Y-m-d")
    end_date = tables.DateColumn(format="Y-m-d")
    actions = tables.TemplateColumn(
        template_code=_LEAVE_ACTIONS,
        orderable=False,
        verbose_name="Actions",
    )

    class Meta:
        """Table meta options."""

        model = Leave
        fields = ("id", "person", "start_date", "end_date", "percentage", "actions")
        attrs = {"class": "table table-striped table-hover"}
