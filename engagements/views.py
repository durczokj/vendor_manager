"""Views for the engagements app."""

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rolepermissions.decorators import has_permission_decorator

from vendor_manager.views import BaseDetailView, BaseListView

from .forms import EngagementForm, EngagementOrderVersionAssignmentForm, EngagementUndertakingAssignmentForm
from .models import Engagement, EngagementOrderVersionAssignment, EngagementUndertakingAssignment


@method_decorator([has_permission_decorator("view_engagement")], name="dispatch")
class EngagementsView(BaseListView):
    """View for listing all engagements and creating a new engagement."""

    model = Engagement
    redirect_to = "engagement"
    form_class = EngagementForm
    template_name_list = "all_engagements.html"
    template_name_add = "add_engagement.html"
    permission_view = "view_engagement"
    permission_manage = "manage_engagement"


@method_decorator([login_required, has_permission_decorator("view_engagement")], name="dispatch")
class EngagementView(BaseDetailView):
    """View for retrieving, updating, and deleting an engagement."""

    model = Engagement
    form_class = EngagementForm
    template_name_details = "engagement_details.html"
    template_name_edit = "edit_engagement.html"
    permission_view = "view_engagement"
    permission_manage = "manage_engagement"
    redirect_to = "engagement"

    def get_related_objects(self, engagement):
        """Return related objects for the engagement."""
        return {"undertaking_assignments": engagement.undertaking_assignments.all()}


@method_decorator([has_permission_decorator("view_engagement")], name="dispatch")
class EngagementUndertakingAssignmentsView(BaseListView):
    """View for listing all engagement undertaking assignments and creating a new engagement undertaking assignment."""

    model = EngagementUndertakingAssignment
    redirect_to = "engagement_undertaking_assignment"
    form_class = EngagementUndertakingAssignmentForm
    template_name_list = "all_engagement_undertaking_assignments.html"
    template_name_add = "add_engagement_undertaking_assignment.html"
    permission_view = "view_engagement_undertaking_assignment"
    permission_manage = "manage_engagement"


@method_decorator([login_required, has_permission_decorator("view_engagement")], name="dispatch")
class EngagementUndertakingAssignmentView(BaseDetailView):
    """View for retrieving, updating, and deleting an engagement undertaking assignment."""

    model = EngagementUndertakingAssignment
    form_class = EngagementUndertakingAssignmentForm
    template_name_details = "engagement_undertaking_assignment_details.html"
    template_name_edit = "edit_engagement_undertaking_assignment.html"
    permission_view = "view_engagement_undertaking_assignment"
    permission_manage = "manage_engagement_undertaking_assignment"
    redirect_to = "engagement_undertaking_assignment"


@method_decorator([has_permission_decorator("view_engagement_order_version_assignment")], name="dispatch")
class EngagementOrderVersionAssignmentsView(BaseListView):
    """View for listing all engagement order version assignments and creating new ones."""

    model = EngagementOrderVersionAssignment
    redirect_to = "engagement_order_version_assignment"
    form_class = EngagementOrderVersionAssignmentForm
    template_name_list = "all_engagement_order_version_assignments.html"
    template_name_add = "add_engagement_order_version_assignment.html"
    permission_view = "view_engagement_order_version_assignment"
    permission_manage = "manage_engagement_order_version_assignment"


@method_decorator([login_required, has_permission_decorator("view_engagement")], name="dispatch")
class EngagementOrderVersionAssignmentView(BaseDetailView):
    """View for retrieving, updating, and deleting an engagement order version assignment."""

    model = EngagementOrderVersionAssignment
    form_class = EngagementOrderVersionAssignmentForm
    template_name_details = "engagement_order_version_assignment_details.html"
    template_name_edit = "edit_engagement_order_version_assignment.html"
    permission_view = "view_engagement_order_version_assignment"
    permission_manage = "manage_engagement_order_version_assignment"
    redirect_to = "engagement_order_version_assignment"
