"""Factory-boy factories for the ``calendars`` app."""

from __future__ import annotations

from datetime import date

import factory

from calendars.models import (
    MON_FRI_MASK,
    Calendar,
    CalendarAssignment,
    HolidayCalendar,
    WeeklyPattern,
)
from people.tests.factories import PersonFactory


class WeeklyPatternFactory(factory.django.DjangoModelFactory):
    """Build a Mon-Fri :class:`WeeklyPattern` with a unique name."""

    class Meta:
        model = WeeklyPattern
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"pattern-{n}")
    working_days = MON_FRI_MASK


class HolidayCalendarFactory(factory.django.DjangoModelFactory):
    """Build a Polish :class:`HolidayCalendar` with a unique name."""

    class Meta:
        model = HolidayCalendar
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"holidays-{n}")
    country_code = "PL"
    subdivision = ""


class CalendarFactory(factory.django.DjangoModelFactory):
    """Build a :class:`Calendar` bundling a WeeklyPattern and HolidayCalendar."""

    class Meta:
        model = Calendar
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"calendar-{n}")
    weekly_pattern = factory.SubFactory(WeeklyPatternFactory)
    holiday_calendar = factory.SubFactory(HolidayCalendarFactory)


class CalendarAssignmentFactory(factory.django.DjangoModelFactory):
    """Build a :class:`CalendarAssignment` spanning all of 2026 by default."""

    class Meta:
        model = CalendarAssignment

    person = factory.SubFactory(PersonFactory)
    calendar = factory.SubFactory(CalendarFactory)
    start_date = date(2026, 1, 1)
    end_date = date(2026, 12, 31)
