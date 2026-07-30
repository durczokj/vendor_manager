"""Views for the leaves app."""

from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView
from rolepermissions.checkers import has_object_permission
from rolepermissions.decorators import has_permission_decorator

from vendor_manager.cbv import EntityDeleteView

from .forms import LeaveForm
from .models import Leave
from .tables import LeaveTable
from .utils.leave_calendar import LeaveCalendar


@method_decorator([has_permission_decorator("view_leave")], name="dispatch")
class LeaveListView(LoginRequiredMixin, ListView):
    """List leaves for the selected month, with a calendar view and create form."""

    model = Leave
    template_name = "leaves.html"

    def get_queryset(self):
        """Return leaves for the current month, filtered by accessibility."""
        month = int(self.request.GET.get("month", datetime.now().month))
        year = int(self.request.GET.get("year", datetime.now().year))
        first_day = datetime(year, month, 1)
        last_day = (
            datetime(year + 1, 1, 1) - timedelta(days=1)
            if month == 12
            else datetime(year, month + 1, 1) - timedelta(days=1)
        )
        qs = Leave.objects.filter(Q(start_date__lte=last_day) & Q(end_date__gte=first_day))
        return [leave for leave in qs if has_object_permission("access_person", self.request.user, leave.person)]

    def get_context_data(self, **kwargs):
        """Add calendar, table, and form to context."""
        ctx = super().get_context_data(**kwargs)
        month = int(self.request.GET.get("month", datetime.now().month))
        year = int(self.request.GET.get("year", datetime.now().year))
        leaves = self.get_queryset()
        ctx.update(
            {
                "table": LeaveTable(leaves),
                "add_url": None,
                "page_title": "Leaves",
                "form": LeaveForm(user=self.request.user),
                "calendar": LeaveCalendar(year=year, month=month, leaves=leaves).formatmonth(),
                "month": month,
                "year": year,
            }
        )
        return ctx


@method_decorator([has_permission_decorator("add_leave")], name="dispatch")
class LeaveCreateView(LoginRequiredMixin, CreateView):
    """Create a new leave request."""

    model = Leave
    form_class = LeaveForm
    success_url = "/leaves/"

    def get_form_kwargs(self):
        """Pass the current user to LeaveForm for person queryset filtering."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_invalid(self, form):
        """Show errors and redirect back to the leave list."""
        messages.error(self.request, form.errors)
        return redirect("leave-list")

    def form_valid(self, form):
        """Save the leave and redirect to the leave list."""
        form.save()
        return redirect("leave-list")


@method_decorator([has_permission_decorator("delete_leave")], name="dispatch")
class LeaveDeleteView(EntityDeleteView):
    """Delete a leave request."""

    model = Leave
    success_url_name = "leave-list"

    def dispatch(self, request, *args, **kwargs):
        """Enforce object-level access check before deleting."""
        leave = get_object_or_404(Leave, pk=kwargs["pk"])
        if not has_object_permission("access_person", request.user, leave.person):
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)
