"""Views for managing undertakings and cost centers."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from rolepermissions.decorators import has_permission_decorator

from vendor_manager.views import BaseDetailView, BaseListView

from .forms import UndertakingForm
from .models import CostCenter, Undertaking


@method_decorator([has_permission_decorator("view_undertaking")], name="dispatch")
class UndertakingsView(BaseListView):
    """View for listing all companies and creating a new company."""

    model = Undertaking
    redirect_to = "undertakings"
    form_class = UndertakingForm
    template_name_list = "all_undertakings.html"
    template_name_add = "add_undertaking.html"
    permission_view = "view_undertaking"
    permission_manage = "manage_undertaking"


@method_decorator([login_required, has_permission_decorator("view_undertaking")], name="dispatch")
class UndertakingView(BaseDetailView):
    """View for retrieving, updating, and deleting a company."""

    model = Undertaking
    form_class = UndertakingForm
    template_name_details = "undertaking_details.html"
    template_name_edit = "edit_undertaking.html"
    permission_view = "view_undertaking"
    permission_manage = "manage_undertaking"
    redirect_to = "undertaking"

    def get_related_objects(self, undertaking):
        """Return related objects for the undertaking."""
        return {
            "engagement_assignments": undertaking.engagement_assignments.all(),
        }


@login_required
def cost_center_details(request, cost_center_id):
    """View to display details of a specific cost center."""
    cost_center = get_object_or_404(CostCenter, id=cost_center_id)
    return render(request, "cost_center_details.html", {"cost_center": cost_center})
