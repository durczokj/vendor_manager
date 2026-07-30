"""Views for managing undertakings and cost centers."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from rolepermissions.decorators import has_permission_decorator

from engagements.tables import EngagementUndertakingAssignmentTable
from vendor_manager.views import BaseDetailView, BaseListView

from .forms import UndertakingForm
from .models import CostCenter, Undertaking
from .tables import UndertakingTable


@method_decorator([has_permission_decorator("view_undertaking")], name="dispatch")
class UndertakingsView(BaseListView):
    """View for listing all companies and creating a new company."""

    model = Undertaking
    redirect_to = "undertakings"
    form_class = UndertakingForm
    permission_view = "view_undertaking"
    permission_manage = "manage_undertaking"
    permission_add = "add_undertaking"
    permission_change = "change_undertaking"
    table_class = UndertakingTable
    page_title = "Undertakings"


@method_decorator([login_required, has_permission_decorator("view_undertaking")], name="dispatch")
class UndertakingView(BaseDetailView):
    """View for retrieving, updating, and deleting a company."""

    model = Undertaking
    form_class = UndertakingForm
    permission_view = "view_undertaking"
    permission_manage = "manage_undertaking"
    permission_change = "change_undertaking"
    permission_delete = "delete_undertaking"
    redirect_to = "undertaking"
    item_url_name = "undertaking"
    list_url_name = "undertakings"
    detail_fields = [("Name", "name"), ("Cost Center", "cost_center"), ("Manager", "manager")]
    related_table_specs = [
        (
            "Engagement Assignments",
            lambda u: u.engagement_assignments.all(),
            EngagementUndertakingAssignmentTable,
        ),
    ]


@login_required
def cost_center_details(request, cost_center_id):
    """View to display details of a specific cost center."""
    cost_center = get_object_or_404(CostCenter, id=cost_center_id)
    return render(request, "cost_center_details.html", {"cost_center": cost_center})
