"""Views for the engagements app."""

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rolepermissions.decorators import has_permission_decorator

from vendor_manager.views import BaseDetailView, BaseListView

from .forms import EngagementForm, EngagementOrderVersionAssignmentForm, EngagementUndertakingAssignmentForm
from .models import Engagement, EngagementOrderVersionAssignment, EngagementUndertakingAssignment
from .tables import (
    EngagementOrderVersionAssignmentTable,
    EngagementTable,
    EngagementUndertakingAssignmentTable,
)


@method_decorator([has_permission_decorator("view_engagement")], name="dispatch")
class EngagementsView(BaseListView):
    """View for listing all engagements and creating a new engagement."""

    model = Engagement
    redirect_to = "engagement"
    form_class = EngagementForm
    permission_view = "view_engagement"
    permission_manage = "manage_engagement"
    permission_add = "add_engagement"
    permission_change = "change_engagement"
    table_class = EngagementTable
    page_title = "Engagements"
    add_url_name = "engagements"


@method_decorator([login_required, has_permission_decorator("view_engagement")], name="dispatch")
class EngagementView(BaseDetailView):
    """View for retrieving, updating, and deleting an engagement."""

    model = Engagement
    form_class = EngagementForm
    permission_view = "view_engagement"
    permission_manage = "manage_engagement"
    permission_change = "change_engagement"
    permission_delete = "delete_engagement"
    redirect_to = "engagement"
    item_url_name = "engagement"
    list_url_name = "engagements"
    detail_fields = [
        ("ID", "id"),
        ("Person", "person"),
        ("Start Date", "start_date"),
        ("End Date", "end_date"),
        ("Daily Rate", "daily_rate"),
        ("FTE", "fte"),
    ]
    related_table_specs = [
        (
            "Undertaking Assignments",
            lambda e: e.undertaking_assignments.all(),
            EngagementUndertakingAssignmentTable,
        ),
    ]


@method_decorator([has_permission_decorator("view_engagement_undertaking_assignment")], name="dispatch")
class EngagementUndertakingAssignmentsView(BaseListView):
    """View for listing all engagement undertaking assignments and creating a new engagement undertaking assignment."""

    model = EngagementUndertakingAssignment
    redirect_to = "engagement_undertaking_assignment"
    form_class = EngagementUndertakingAssignmentForm
    permission_view = "view_engagement_undertaking_assignment"
    permission_manage = "manage_engagement"
    permission_add = "add_engagement_undertaking_assignment"
    permission_change = "change_engagement_undertaking_assignment"
    table_class = EngagementUndertakingAssignmentTable
    page_title = "Engagement Undertaking Assignments"
    add_url_name = "engagement_undertaking_assignments"


@method_decorator([login_required, has_permission_decorator("view_engagement_undertaking_assignment")], name="dispatch")
class EngagementUndertakingAssignmentView(BaseDetailView):
    """View for retrieving, updating, and deleting an engagement undertaking assignment."""

    model = EngagementUndertakingAssignment
    form_class = EngagementUndertakingAssignmentForm
    permission_view = "view_engagement_undertaking_assignment"
    permission_manage = "manage_engagement_undertaking_assignment"
    permission_change = "change_engagement_undertaking_assignment"
    permission_delete = "delete_engagement_undertaking_assignment"
    redirect_to = "engagement_undertaking_assignment"
    item_url_name = "engagement_undertaking_assignment"
    list_url_name = "engagement_undertaking_assignments"
    detail_fields = [
        ("ID", "id"),
        ("Engagement", "engagement"),
        ("Undertaking", "undertaking"),
        ("Percentage", "percentage"),
        ("Start Date", "start_date"),
        ("End Date", "end_date"),
    ]


@method_decorator([has_permission_decorator("view_engagement_order_version_assignment")], name="dispatch")
class EngagementOrderVersionAssignmentsView(BaseListView):
    """View for listing all engagement order version assignments and creating new ones."""

    model = EngagementOrderVersionAssignment
    redirect_to = "engagement_order_version_assignment"
    form_class = EngagementOrderVersionAssignmentForm
    permission_view = "view_engagement_order_version_assignment"
    permission_manage = "manage_engagement_order_version_assignment"
    permission_add = "add_engagement_order_version_assignment"
    permission_change = "change_engagement_order_version_assignment"
    table_class = EngagementOrderVersionAssignmentTable
    page_title = "Engagement Order Version Assignments"
    add_url_name = "engagement_order_version_assignments"


@method_decorator(
    [login_required, has_permission_decorator("view_engagement_order_version_assignment")], name="dispatch"
)
class EngagementOrderVersionAssignmentView(BaseDetailView):
    """View for retrieving, updating, and deleting an engagement order version assignment."""

    model = EngagementOrderVersionAssignment
    form_class = EngagementOrderVersionAssignmentForm
    permission_view = "view_engagement_order_version_assignment"
    permission_manage = "manage_engagement_order_version_assignment"
    permission_change = "change_engagement_order_version_assignment"
    permission_delete = "delete_engagement_order_version_assignment"
    redirect_to = "engagement_order_version_assignment"
    item_url_name = "engagement_order_version_assignment"
    list_url_name = "engagement_order_version_assignments"
    detail_fields = [
        ("ID", "id"),
        ("Engagement", "engagement"),
        ("Order Version", "order_version"),
    ]
