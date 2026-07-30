"""Views for managing undertakings and cost centers."""

from django.utils.decorators import method_decorator
from rolepermissions.decorators import has_permission_decorator

from engagements.tables import EngagementUndertakingAssignmentTable
from vendor_manager.cbv import EntityCreateView, EntityDeleteView, EntityDetailView, EntityListView, EntityUpdateView

from .forms import UndertakingForm
from .models import Undertaking
from .tables import UndertakingTable


@method_decorator([has_permission_decorator("view_undertaking")], name="dispatch")
class UndertakingListView(EntityListView):
    """List all undertakings."""

    model = Undertaking
    table_class = UndertakingTable
    page_title = "Undertakings"
    permission_create = "add_undertaking"
    create_url_name = "undertaking-create"


@method_decorator([has_permission_decorator("view_undertaking")], name="dispatch")
class UndertakingDetailView(EntityDetailView):
    """Show a single undertaking."""

    model = Undertaking
    permission_change = "change_undertaking"
    update_url_name = "undertaking-update"
    delete_url_name = "undertaking-delete"
    list_url_name = "undertaking-list"
    detail_fields = [("Name", "name"), ("Cost Center", "cost_center"), ("Manager", "manager")]
    related_table_specs = [
        ("Engagement Assignments", lambda u: u.engagement_assignments.all(), EngagementUndertakingAssignmentTable),
    ]


@method_decorator([has_permission_decorator("add_undertaking")], name="dispatch")
class UndertakingCreateView(EntityCreateView):
    """Create a new undertaking."""

    model = Undertaking
    form_class = UndertakingForm
    success_url_name = "undertaking-detail"
    list_url_name = "undertaking-list"


@method_decorator([has_permission_decorator("change_undertaking")], name="dispatch")
class UndertakingUpdateView(EntityUpdateView):
    """Edit an existing undertaking."""

    model = Undertaking
    form_class = UndertakingForm
    success_url_name = "undertaking-detail"


@method_decorator([has_permission_decorator("delete_undertaking")], name="dispatch")
class UndertakingDeleteView(EntityDeleteView):
    """Delete an undertaking."""

    model = Undertaking
    success_url_name = "undertaking-list"
