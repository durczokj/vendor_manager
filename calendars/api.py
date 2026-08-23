"""Viewsets for the calendars app.

Admins hold full CRUD on all four models. Undertaking Managers hold
read-only access to :class:`Calendar`, :class:`HolidayCalendar` and
:class:`WeeklyPattern`, and full CRUD on :class:`CalendarAssignment`
restricted at the object level to persons they can access (see
:func:`people.permissions.access_person`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rolepermissions.checkers import has_object_permission

from calendars.filters import (
    CalendarAssignmentFilterSet,
    CalendarFilterSet,
    HolidayCalendarFilterSet,
    WeeklyPatternFilterSet,
)
from calendars.models import Calendar, CalendarAssignment, HolidayCalendar, WeeklyPattern
from calendars.permissions import CanAccessAssignmentPerson, HasRolePermission
from calendars.serializers import (
    CalendarAssignmentSerializer,
    CalendarSerializer,
    HolidayCalendarSerializer,
    WeeklyPatternSerializer,
)
from people.models import Person
from vendor_manager.api_permissions import HasLinkedPerson

if TYPE_CHECKING:
    from rest_framework.serializers import BaseSerializer


class WeeklyPatternViewSet(viewsets.ModelViewSet[WeeklyPattern]):
    """WeeklyPattern list/create/retrieve/update/destroy endpoints."""

    queryset = WeeklyPattern.objects.all().order_by("id")
    serializer_class = WeeklyPatternSerializer
    filterset_class = WeeklyPatternFilterSet
    search_fields = ["name"]
    ordering_fields = ["id", "name", "working_days"]
    permission_classes = [IsAuthenticated, HasLinkedPerson, HasRolePermission]
    rp_model_name = "weeklypattern"


class HolidayCalendarViewSet(viewsets.ModelViewSet[HolidayCalendar]):
    """HolidayCalendar list/create/retrieve/update/destroy endpoints."""

    queryset = HolidayCalendar.objects.all().order_by("id")
    serializer_class = HolidayCalendarSerializer
    filterset_class = HolidayCalendarFilterSet
    search_fields = ["name", "country_code", "subdivision"]
    ordering_fields = ["id", "name", "country_code"]
    permission_classes = [IsAuthenticated, HasLinkedPerson, HasRolePermission]
    rp_model_name = "holidaycalendar"


class CalendarViewSet(viewsets.ModelViewSet[Calendar]):
    """Calendar list/create/retrieve/update/destroy endpoints."""

    queryset = Calendar.objects.all().select_related("weekly_pattern", "holiday_calendar").order_by("id")
    serializer_class = CalendarSerializer
    filterset_class = CalendarFilterSet
    search_fields = ["name"]
    ordering_fields = ["id", "name"]
    permission_classes = [IsAuthenticated, HasLinkedPerson, HasRolePermission]
    rp_model_name = "calendar"


class CalendarAssignmentViewSet(viewsets.ModelViewSet[CalendarAssignment]):
    """CalendarAssignment list/create/retrieve/update/destroy endpoints.

    Overlap validation runs in :meth:`CalendarAssignment.clean` (invoked via
    the model's ``save`` override), so invalid POSTs surface as ``400``
    responses. Undertaking Managers can only write assignments for persons
    they can access via :func:`people.permissions.access_person`.
    """

    serializer_class = CalendarAssignmentSerializer
    filterset_class = CalendarAssignmentFilterSet
    search_fields = ["person__id", "person__first_name", "person__last_name", "calendar__name"]
    ordering_fields = ["id", "person", "start_date", "end_date"]
    permission_classes = [
        IsAuthenticated,
        HasLinkedPerson,
        HasRolePermission,
        CanAccessAssignmentPerson,
    ]
    rp_model_name = "calendarassignment"

    def get_queryset(self) -> Any:
        """Scope list/detail to assignments whose person the caller can access."""
        base = CalendarAssignment.objects.all().select_related("person", "calendar").order_by("id")
        user = self.request.user
        if not user.is_authenticated:
            return base.none()
        return base.filter(person__in=Person.objects.accessible_to(user))

    def perform_create(self, serializer: BaseSerializer[CalendarAssignment]) -> None:
        """Enforce the ``access_person`` object check on the target person."""
        person = serializer.validated_data.get("person")
        if person is not None and not has_object_permission("access_person", self.request.user, person):
            raise PermissionDenied("You do not have permission to assign a calendar to this person.")
        serializer.save()
