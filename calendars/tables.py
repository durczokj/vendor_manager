"""django-tables2 tables for the calendars app UI."""

import django_tables2 as tables

from vendor_manager.tables import BaseEntityTable

from .models import CalendarAssignment

_ASSIGNMENT_ACTIONS = """
{% if table.can_manage %}
<a href="{% url 'calendar-assignment-update' record.pk %}" class="inline"><button>Edit</button></a>
<a href="{% url 'calendar-assignment-delete' record.pk %}" class="inline"><button>Delete</button></a>
{% endif %}
"""


class CalendarAssignmentTable(BaseEntityTable):
    """Table for listing :class:`CalendarAssignment` records."""

    id = tables.Column(linkify=("calendar-assignment-detail", {"pk": tables.A("pk")}))
    person = tables.Column(linkify=("person-detail", {"pk": tables.A("person.pk")}))
    calendar = tables.Column()
    start_date = tables.DateColumn(format="Y-m-d")
    end_date = tables.DateColumn(format="Y-m-d")
    actions = tables.TemplateColumn(
        template_code=_ASSIGNMENT_ACTIONS,
        orderable=False,
        verbose_name="Actions",
    )

    class Meta:
        """Table meta options."""

        model = CalendarAssignment
        fields = ("id", "person", "calendar", "start_date", "end_date", "actions")
        attrs = {"class": "table table-striped table-hover"}
