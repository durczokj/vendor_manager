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

from people.models import Person
from undertakings.models import Undertaking
from vendor_manager.cbv import EntityDeleteView

from .forms import LeaveForm
from .models import Leave
from .tables import LeaveTable
from .utils.leave_calendar import LeaveCalendar
from .utils.leave_matrix import LeaveMatrix

_VALID_VIEWS = {"calendar", "matrix"}
_DEFAULT_VIEW = "matrix"


@method_decorator([has_permission_decorator("view_leave")], name="dispatch")
class LeaveListView(LoginRequiredMixin, ListView):
    """List leaves for the selected month, with a calendar/matrix view and create form."""

    model = Leave
    template_name = "leaves.html"

    def _resolve_undertaking_id(self) -> int | None:
        """Parse ``?undertaking=<pk>`` from the querystring; return None if absent/invalid."""
        raw = self.request.GET.get("undertaking", "").strip()
        if not raw:
            return None
        try:
            return int(raw)
        except ValueError:
            return None

    def _resolve_view(self) -> str:
        """Parse ``?view=calendar|matrix``; default to ``matrix``."""
        raw = self.request.GET.get("view", _DEFAULT_VIEW).strip().lower()
        return raw if raw in _VALID_VIEWS else _DEFAULT_VIEW

    def _resolve_include_all_people(self) -> bool:
        """Parse ``?include_all_people=on`` (checkbox); default False."""
        raw = self.request.GET.get("include_all_people", "").strip().lower()
        return raw in {"1", "on", "true", "yes"}

    def get_queryset(self):
        """Return leaves for the current month, filtered by accessibility and undertaking."""
        month = int(self.request.GET.get("month", datetime.now().month))
        year = int(self.request.GET.get("year", datetime.now().year))
        first_day = datetime(year, month, 1)
        last_day = (
            datetime(year + 1, 1, 1) - timedelta(days=1)
            if month == 12
            else datetime(year, month + 1, 1) - timedelta(days=1)
        )
        qs = Leave.objects.filter(Q(start_date__lte=last_day) & Q(end_date__gte=first_day))

        undertaking_id = self._resolve_undertaking_id()
        if undertaking_id is not None:
            # A person is "assigned to" an undertaking if any of their engagements has
            # an EngagementUndertakingAssignment pointing at it that overlaps the month.
            qs = qs.filter(
                person__engagements__undertaking_assignments__undertaking_id=undertaking_id,
                person__engagements__undertaking_assignments__start_date__lte=last_day,
                person__engagements__undertaking_assignments__end_date__gte=first_day,
            ).distinct()

        return [leave for leave in qs if has_object_permission("access_person", self.request.user, leave.person)]

    def _people_for_matrix(self, undertaking_id: int | None, first_day, last_day) -> list[Person]:
        """Return the people whose rows should appear in the matrix when 'include all' is on.

        Scope is limited to people the user can see; if an undertaking filter is
        active, we further narrow to people assigned to that undertaking during
        the displayed month.
        """
        people_qs = Person.objects.accessible_to(self.request.user)
        if undertaking_id is not None:
            people_qs = people_qs.filter(
                engagements__undertaking_assignments__undertaking_id=undertaking_id,
                engagements__undertaking_assignments__start_date__lte=last_day,
                engagements__undertaking_assignments__end_date__gte=first_day,
            ).distinct()
        return list(people_qs.order_by("first_name", "last_name"))

    def get_context_data(self, **kwargs):
        """Add calendar/matrix, table, form, and filter selections to context."""
        ctx = super().get_context_data(**kwargs)
        month = int(self.request.GET.get("month", datetime.now().month))
        year = int(self.request.GET.get("year", datetime.now().year))
        first_day = datetime(year, month, 1)
        last_day = (
            datetime(year + 1, 1, 1) - timedelta(days=1)
            if month == 12
            else datetime(year, month + 1, 1) - timedelta(days=1)
        )
        leaves = self.get_queryset()
        view_mode = self._resolve_view()
        selected_undertaking_id = self._resolve_undertaking_id()
        include_all_people = self._resolve_include_all_people()

        undertakings = Undertaking.objects.accessible_to(self.request.user).order_by("name")
        matrix_people = (
            self._people_for_matrix(selected_undertaking_id, first_day, last_day) if include_all_people else None
        )

        ctx.update(
            {
                "table": LeaveTable(leaves),
                "add_url": None,
                "page_title": "Leaves",
                "form": LeaveForm(user=self.request.user),
                "calendar": LeaveCalendar(year=year, month=month, leaves=leaves).formatmonth(),
                "matrix": LeaveMatrix(year=year, month=month, leaves=leaves, people=matrix_people).render(),
                "month": month,
                "year": year,
                "view_mode": view_mode,
                "undertakings": undertakings,
                "selected_undertaking_id": selected_undertaking_id,
                "include_all_people": include_all_people,
            }
        )
        return ctx


@method_decorator([has_permission_decorator("add_leave")], name="dispatch")
class LeaveCreateView(LoginRequiredMixin, CreateView):
    """Create a new leave request."""

    model = Leave
    form_class = LeaveForm
    template_name = "_form.html"
    success_url = "/leaves/"

    def get_form_kwargs(self):
        """Pass the current user to LeaveForm for person queryset filtering."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Inject the context keys the shared _form.html expects."""
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "page_title": "Add Leave",
                "submit_label": "Save",
                "cancel_url": "/leaves/",
                "form_action": self.request.path,
            }
        )
        return ctx

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
