"""Views for managing undertakings and cost centers."""

import json

from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views import View
from rolepermissions.checkers import has_permission
from rolepermissions.decorators import has_permission_decorator

from vendor_manager.utils.is_api_request import is_api_request
from vendor_manager.views import BaseListView

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
class UndertakingView(View):
    """View for retrieving, updating, and deleting an undertaking."""

    @method_decorator([has_permission_decorator("view_undertaking")])
    def get(self, request, undertaking_id):
        """Retrieve undertaking details."""
        undertaking = get_object_or_404(Undertaking, id=undertaking_id)
        if request.GET.get("form") == "True":
            return self.__get_edit_form(request, undertaking)
        return self.__get_details(request, undertaking)

    @method_decorator([has_permission_decorator("view_undertaking")])
    def __get_details(self, request, undertaking):
        engagement_assignments = undertaking.engagement_assignments.all()
        if is_api_request(request):
            return JsonResponse({"id": undertaking.id, "name": undertaking.name})
        return render(
            request,
            "undertaking_details.html",
            {
                "undertaking": undertaking,
                "engagement_assignments": engagement_assignments,
                "manage_undertaking": has_permission(request.user, "manage_undertaking"),
            },
        )

    @method_decorator([has_permission_decorator("manage_undertaking")])
    def __get_edit_form(self, request, undertaking):
        form = UndertakingForm(instance=undertaking)
        return render(request, "edit_undertaking.html", {"form": form, "undertaking": undertaking})

    @method_decorator([has_permission_decorator("manage_undertaking")])
    def put(self, request, undertaking_id):
        """Update undertaking details."""
        undertaking = get_object_or_404(Undertaking, id=undertaking_id)
        if is_api_request(request):
            data = json.loads(request.body)
        else:
            data = request.POST
        for field in model_to_dict(undertaking).keys():
            if field in data:
                setattr(undertaking, field, data[field])
        undertaking.save()
        if is_api_request(request):
            return JsonResponse({"message": "Undertaking updated successfully"})
        else:
            return self.get(request, undertaking_id)

    @method_decorator([has_permission_decorator("manage_undertaking")])
    def post(self, request, undertaking_id):
        """Create a new engagement assignment for the undertaking."""
        return self.put(request, undertaking_id)

    @method_decorator([has_permission_decorator("manage_undertaking")])
    def delete(self, request, undertaking_id):
        """Delete an undertaking."""
        undertaking = get_object_or_404(Undertaking, id=undertaking_id)
        undertaking.delete()
        return JsonResponse({"message": "Undertaking deleted successfully"})


@login_required
def cost_center_details(request, cost_center_id):
    """View to display details of a specific cost center."""
    cost_center = get_object_or_404(CostCenter, id=cost_center_id)
    return render(request, "cost_center_details.html", {"cost_center": cost_center})
