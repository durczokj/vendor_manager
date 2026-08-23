"""Managers and querysets for the calendars app."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.models import User
from django.db import models

from people.models import Person

if TYPE_CHECKING:
    from calendars.models import CalendarAssignment

    _CalendarAssignmentQuerySetBase = models.QuerySet[CalendarAssignment]
else:
    _CalendarAssignmentQuerySetBase = models.QuerySet


class CalendarAssignmentQuerySet(_CalendarAssignmentQuerySetBase):
    """QuerySet for :class:`CalendarAssignment` scoped by the assigned person."""

    def accessible_to(self, user: User) -> CalendarAssignmentQuerySet:
        """Return assignments whose ``person`` is accessible to ``user``."""
        return self.filter(person__in=Person.objects.accessible_to(user))


CalendarAssignmentManager = models.Manager.from_queryset(CalendarAssignmentQuerySet)
