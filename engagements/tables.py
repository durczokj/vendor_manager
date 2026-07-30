"""django-tables2 table classes for the engagements app."""

import django_tables2 as tables

from vendor_manager.tables import BaseEntityTable

from .models import Engagement, EngagementOrderVersionAssignment, EngagementUndertakingAssignment

_ENGAGEMENT_ACTIONS = """
{% if table.can_manage %}
<a href="{% url 'engagement-update' record.pk %}" class="inline"><button>Edit</button></a>
<a href="{% url 'engagement-delete' record.pk %}" class="inline"><button>Delete</button></a>
{% endif %}
"""

_EUA_ACTIONS = """
{% if table.can_manage %}
<a href="{% url 'engagement-undertaking-assignment-update' record.pk %}" class="inline"><button>Edit</button></a>
<a href="{% url 'engagement-undertaking-assignment-delete' record.pk %}" class="inline"><button>Delete</button></a>
{% endif %}
"""

_EOVA_ACTIONS = """
{% if table.can_manage %}
<a href="{% url 'engagement-order-version-assignment-update' record.pk %}" class="inline"><button>Edit</button></a>
<a href="{% url 'engagement-order-version-assignment-delete' record.pk %}" class="inline"><button>Delete</button></a>
{% endif %}
"""


class EngagementTable(BaseEntityTable):
    """Table for listing Engagement records."""

    id = tables.Column(linkify=("engagement-detail", {"pk": tables.A("pk")}))
    start_date = tables.DateColumn(format="Y-m-d")
    end_date = tables.DateColumn(format="Y-m-d")
    actions = tables.TemplateColumn(
        template_code=_ENGAGEMENT_ACTIONS,
        orderable=False,
        verbose_name="Actions",
    )

    class Meta:
        """Table meta options."""

        model = Engagement
        fields = ("id", "person", "start_date", "end_date", "daily_rate", "fte", "actions")
        attrs = {"class": "table table-striped table-hover"}


class EngagementUndertakingAssignmentTable(BaseEntityTable):
    """Table for listing EngagementUndertakingAssignment records."""

    id = tables.Column(linkify=("engagement-undertaking-assignment-detail", {"pk": tables.A("pk")}))
    start_date = tables.DateColumn(format="Y-m-d")
    end_date = tables.DateColumn(format="Y-m-d")
    actions = tables.TemplateColumn(
        template_code=_EUA_ACTIONS,
        orderable=False,
        verbose_name="Actions",
    )

    class Meta:
        """Table meta options."""

        model = EngagementUndertakingAssignment
        fields = ("id", "engagement", "undertaking", "percentage", "start_date", "end_date", "actions")
        attrs = {"class": "table table-striped table-hover"}


class EngagementOrderVersionAssignmentTable(BaseEntityTable):
    """Table for listing EngagementOrderVersionAssignment records."""

    id = tables.Column(linkify=("engagement-order-version-assignment-detail", {"pk": tables.A("pk")}))
    actions = tables.TemplateColumn(
        template_code=_EOVA_ACTIONS,
        orderable=False,
        verbose_name="Actions",
    )

    class Meta:
        """Table meta options."""

        model = EngagementOrderVersionAssignment
        fields = ("id", "engagement", "order_version", "actions")
        attrs = {"class": "table table-striped table-hover"}
