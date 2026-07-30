"""Views for EngagementOrderVersionAssignment (split from views.py to stay < 150 lines)."""

from django.utils.decorators import method_decorator
from rolepermissions.decorators import has_permission_decorator

from vendor_manager.cbv import EntityCreateView, EntityDeleteView, EntityDetailView, EntityListView, EntityUpdateView

from .forms import EngagementOrderVersionAssignmentForm
from .models import EngagementOrderVersionAssignment
from .tables import EngagementOrderVersionAssignmentTable


@method_decorator([has_permission_decorator("view_engagement_order_version_assignment")], name="dispatch")
class EngagementOrderVersionAssignmentListView(EntityListView):
    """List all engagement–order-version assignments."""

    model = EngagementOrderVersionAssignment
    table_class = EngagementOrderVersionAssignmentTable
    page_title = "Engagement Order Version Assignments"
    permission_create = "add_engagement_order_version_assignment"
    create_url_name = "engagement-order-version-assignment-create"


@method_decorator([has_permission_decorator("view_engagement_order_version_assignment")], name="dispatch")
class EngagementOrderVersionAssignmentDetailView(EntityDetailView):
    """Show a single engagement–order-version assignment."""

    model = EngagementOrderVersionAssignment
    permission_change = "change_engagement_order_version_assignment"
    update_url_name = "engagement-order-version-assignment-update"
    delete_url_name = "engagement-order-version-assignment-delete"
    list_url_name = "engagement-order-version-assignment-list"
    detail_fields = [
        ("ID", "id"),
        ("Engagement", "engagement"),
        ("Order Version", "order_version"),
    ]


@method_decorator([has_permission_decorator("add_engagement_order_version_assignment")], name="dispatch")
class EngagementOrderVersionAssignmentCreateView(EntityCreateView):
    """Create a new engagement–order-version assignment."""

    model = EngagementOrderVersionAssignment
    form_class = EngagementOrderVersionAssignmentForm
    success_url_name = "engagement-order-version-assignment-detail"
    list_url_name = "engagement-order-version-assignment-list"


@method_decorator([has_permission_decorator("change_engagement_order_version_assignment")], name="dispatch")
class EngagementOrderVersionAssignmentUpdateView(EntityUpdateView):
    """Edit an existing engagement–order-version assignment."""

    model = EngagementOrderVersionAssignment
    form_class = EngagementOrderVersionAssignmentForm
    success_url_name = "engagement-order-version-assignment-detail"


@method_decorator([has_permission_decorator("delete_engagement_order_version_assignment")], name="dispatch")
class EngagementOrderVersionAssignmentDeleteView(EntityDeleteView):
    """Delete an engagement–order-version assignment."""

    model = EngagementOrderVersionAssignment
    success_url_name = "engagement-order-version-assignment-list"
