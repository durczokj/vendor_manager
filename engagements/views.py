"""Views for the engagements app."""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views import View
from rolepermissions.checkers import has_permission
from rolepermissions.decorators import has_permission_decorator

from vendor_manager.utils.is_api_request import is_api_request
from vendor_manager.views import BaseListView

from .forms import EngagementForm
from .models import Engagement


@method_decorator([has_permission_decorator("view_engagement")], name="dispatch")
class EngagementsView(BaseListView):
    """View for listing all companies and creating a new company."""

    model = Engagement
    redirect_to = "engagements"
    form_class = EngagementForm
    template_name_list = "all_engagements.html"
    template_name_add = "add_engagement.html"
    permission_view = "view_engagement"
    permission_manage = "manage_engagement"


@method_decorator([login_required, has_permission_decorator("view_engagement")], name="dispatch")
class EngagementView(View):
    """View for retrieving, updating, and deleting an engagement."""

    @method_decorator([has_permission_decorator("view_engagement")])
    def get(self, request, engagement_id):
        """Retrieve engagement details."""
        engagement = get_object_or_404(Engagement, id=engagement_id)
        if request.GET.get("form") == "True":
            return self.__get_edit_form(request, engagement)
        return self.__get_details(request, engagement)

    @method_decorator([has_permission_decorator("view_engagement")])
    def __get_details(self, request, engagement):
        assignments = engagement.undertaking_assignments.all()
        if is_api_request(request):
            return JsonResponse({"id": engagement.id, "name": engagement.name})
        return render(
            request,
            "engagement_details.html",
            {
                "engagement": engagement,
                "assignments": assignments,
                "manage_engagement": has_permission(request.user, "manage_engagement"),
            },
        )

    @method_decorator([has_permission_decorator("manage_engagement")])
    def __get_edit_form(self, request, engagement):
        form = EngagementForm(instance=engagement)
        return render(request, "edit_engagement.html", {"form": form, "engagement": engagement})

    @method_decorator([has_permission_decorator("manage_engagement")])
    def put(self, request, engagement_id):
        """Update engagement details."""
        engagement = get_object_or_404(Engagement, id=engagement_id)
        return EngagementsView()._handle_form(request, engagement)

    @method_decorator([has_permission_decorator("manage_engagement")])
    def post(self, request, engagement_id):
        """Create a new assignment for the engagement."""
        return self.put(request, engagement_id)

    @method_decorator([has_permission_decorator("manage_engagement")])
    def delete(self, request, engagement_id):
        """Delete an engagement."""
        engagement = get_object_or_404(Engagement, id=engagement_id)
        engagement.delete()
        return JsonResponse({"message": "Engagement deleted successfully"})
