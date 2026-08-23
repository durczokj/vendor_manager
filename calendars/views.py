"""Views for the calendars app UI (CalendarAssignment CRUD).

Calendar / HolidayCalendar / WeeklyPattern templates are maintained via the
Django admin and the REST API. Only :class:`CalendarAssignment` gets a UI
CRUD flow, as those are edited routinely by admins and undertaking
managers.
"""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest, HttpResponseForbidden
from django.http.response import HttpResponseBase
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from rolepermissions.checkers import has_object_permission
from rolepermissions.decorators import has_permission_decorator

from vendor_manager.cbv import EntityCreateView, EntityDeleteView, EntityDetailView, EntityListView, EntityUpdateView

from .forms import CalendarAssignmentForm
from .models import CalendarAssignment
from .tables import CalendarAssignmentTable


def _forbid_if_not_accessible(request: HttpRequest, assignment: CalendarAssignment) -> HttpResponseBase | None:
    """Return a 403 response if the caller cannot access the assignment's person."""
    if not has_object_permission("access_person", request.user, assignment.person):
        return HttpResponseForbidden()
    return None


@method_decorator([has_permission_decorator("view_calendarassignment")], name="dispatch")
class CalendarAssignmentListView(EntityListView):
    """List calendar assignments accessible to the user."""

    model = CalendarAssignment
    table_class = CalendarAssignmentTable
    page_title = "Calendar Assignments"
    permission_create = "add_calendarassignment"
    create_url_name = "calendar-assignment-create"


@method_decorator([has_permission_decorator("view_calendarassignment")], name="dispatch")
class CalendarAssignmentDetailView(EntityDetailView):
    """Show a single calendar assignment."""

    model = CalendarAssignment
    permission_change = "change_calendarassignment"
    update_url_name = "calendar-assignment-update"
    delete_url_name = "calendar-assignment-delete"
    list_url_name = "calendar-assignment-list"
    detail_fields = [
        ("Person", "person", "person-detail"),
        ("Calendar", "calendar"),
        ("Start date", "start_date"),
        ("End date", "end_date"),
    ]


@method_decorator([has_permission_decorator("add_calendarassignment")], name="dispatch")
class CalendarAssignmentCreateView(EntityCreateView):
    """Create a new calendar assignment (person is required in the form)."""

    model = CalendarAssignment
    form_class = CalendarAssignmentForm
    success_url_name = "calendar-assignment-detail"
    list_url_name = "calendar-assignment-list"

    def form_valid(self, form: Any) -> Any:
        """Reject saves for persons the caller cannot access."""
        person = form.cleaned_data.get("person")
        if person is not None and not has_object_permission("access_person", self.request.user, person):
            return HttpResponseForbidden()
        return super().form_valid(form)


@method_decorator([has_permission_decorator("change_calendarassignment")], name="dispatch")
class CalendarAssignmentUpdateView(EntityUpdateView):
    """Edit an existing calendar assignment."""

    model = CalendarAssignment
    form_class = CalendarAssignmentForm
    success_url_name = "calendar-assignment-detail"

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
        """Reject edits when the caller cannot access the assignment's person."""
        assignment = get_object_or_404(CalendarAssignment, pk=kwargs["pk"])
        forbidden = _forbid_if_not_accessible(request, assignment)
        if forbidden is not None:
            return forbidden
        return super().dispatch(request, *args, **kwargs)


@method_decorator([has_permission_decorator("delete_calendarassignment")], name="dispatch")
class CalendarAssignmentDeleteView(EntityDeleteView):
    """Delete a calendar assignment."""

    model = CalendarAssignment
    success_url_name = "calendar-assignment-list"

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
        """Reject deletes when the caller cannot access the assignment's person."""
        assignment = get_object_or_404(CalendarAssignment, pk=kwargs["pk"])
        forbidden = _forbid_if_not_accessible(request, assignment)
        if forbidden is not None:
            return forbidden
        return super().dispatch(request, *args, **kwargs)
