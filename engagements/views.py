"""Views for the engagements app."""

from django.utils.decorators import method_decorator
from rolepermissions.decorators import has_permission_decorator

from vendor_manager.cbv import EntityCreateView, EntityDeleteView, EntityDetailView, EntityListView, EntityUpdateView

from .forms import EngagementForm, EngagementUndertakingAssignmentForm
from .models import Engagement, EngagementUndertakingAssignment
from .tables import EngagementTable, EngagementUndertakingAssignmentTable


@method_decorator([has_permission_decorator("view_engagement")], name="dispatch")
class EngagementListView(EntityListView):
    """List all engagements."""

    model = Engagement
    table_class = EngagementTable
    page_title = "Engagements"
    permission_create = "add_engagement"
    create_url_name = "engagement-create"


@method_decorator([has_permission_decorator("view_engagement")], name="dispatch")
class EngagementDetailView(EntityDetailView):
    """Show a single engagement."""

    model = Engagement
    permission_change = "change_engagement"
    update_url_name = "engagement-update"
    delete_url_name = "engagement-delete"
    list_url_name = "engagement-list"
    detail_fields = [
        ("ID", "id"),
        ("Person", "person", "person-detail"),
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
            "engagement-undertaking-assignment-create",
            "add_engagement_undertaking_assignment",
        ),
    ]


@method_decorator([has_permission_decorator("add_engagement")], name="dispatch")
class EngagementCreateView(EntityCreateView):
    """Create a new engagement."""

    model = Engagement
    form_class = EngagementForm
    success_url_name = "engagement-detail"
    list_url_name = "engagement-list"


@method_decorator([has_permission_decorator("change_engagement")], name="dispatch")
class EngagementUpdateView(EntityUpdateView):
    """Edit an existing engagement (calls update_engagement service via form.save)."""

    model = Engagement
    form_class = EngagementForm
    success_url_name = "engagement-detail"


@method_decorator([has_permission_decorator("delete_engagement")], name="dispatch")
class EngagementDeleteView(EntityDeleteView):
    """Delete an engagement."""

    model = Engagement
    success_url_name = "engagement-list"


@method_decorator([has_permission_decorator("view_engagement_undertaking_assignment")], name="dispatch")
class EngagementUndertakingAssignmentListView(EntityListView):
    """List all engagement–undertaking assignments."""

    model = EngagementUndertakingAssignment
    table_class = EngagementUndertakingAssignmentTable
    page_title = "Engagement Undertaking Assignments"
    permission_create = "add_engagement_undertaking_assignment"
    create_url_name = "engagement-undertaking-assignment-create"


@method_decorator([has_permission_decorator("view_engagement_undertaking_assignment")], name="dispatch")
class EngagementUndertakingAssignmentDetailView(EntityDetailView):
    """Show a single engagement–undertaking assignment."""

    model = EngagementUndertakingAssignment
    permission_change = "change_engagement_undertaking_assignment"
    update_url_name = "engagement-undertaking-assignment-update"
    delete_url_name = "engagement-undertaking-assignment-delete"
    list_url_name = "engagement-undertaking-assignment-list"
    detail_fields = [
        ("ID", "id"),
        ("Engagement", "engagement", "engagement-detail"),
        ("Undertaking", "undertaking", "undertaking-detail"),
        ("Percentage", "percentage"),
        ("Start Date", "start_date"),
        ("End Date", "end_date"),
    ]


@method_decorator([has_permission_decorator("add_engagement_undertaking_assignment")], name="dispatch")
class EngagementUndertakingAssignmentCreateView(EntityCreateView):
    """Create a new engagement–undertaking assignment."""

    model = EngagementUndertakingAssignment
    form_class = EngagementUndertakingAssignmentForm
    success_url_name = "engagement-undertaking-assignment-detail"
    list_url_name = "engagement-undertaking-assignment-list"


@method_decorator([has_permission_decorator("change_engagement_undertaking_assignment")], name="dispatch")
class EngagementUndertakingAssignmentUpdateView(EntityUpdateView):
    """Edit an existing engagement–undertaking assignment."""

    model = EngagementUndertakingAssignment
    form_class = EngagementUndertakingAssignmentForm
    success_url_name = "engagement-undertaking-assignment-detail"


@method_decorator([has_permission_decorator("delete_engagement_undertaking_assignment")], name="dispatch")
class EngagementUndertakingAssignmentDeleteView(EntityDeleteView):
    """Delete an engagement–undertaking assignment."""

    model = EngagementUndertakingAssignment
    success_url_name = "engagement-undertaking-assignment-list"
