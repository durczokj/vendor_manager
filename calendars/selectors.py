"""Pure-function selectors for the calendars app.

Free-vs-working days are computed on demand from the two components of a
:class:`~calendars.models.Calendar` (its :class:`WeeklyPattern` and its
:class:`HolidayCalendar`). Only the *declarations* are persisted; the
actual dates are derived here.

Person-scoped helpers resolve the applicable :class:`Calendar` for a given
date via :class:`~calendars.models.CalendarAssignment` (time-scoped).

The holiday set for a given ``(country, subdivision, year)`` triple is
cached per process with :func:`functools.cache`; it is safe to hold
because the underlying ``python-holidays`` data is a pure function of
those inputs.
"""

from __future__ import annotations

from datetime import date, timedelta
from functools import cache
from typing import TYPE_CHECKING, Any

import holidays as holidays_lib

if TYPE_CHECKING:
    from calendars.models import Calendar
    from people.models import Person


@cache
def _holidays_for_year(country_code: str, subdivision: str, year: int) -> frozenset[date]:
    """Return the set of holiday dates for a country/subdivision in ``year``.

    Args:
        country_code: ISO-3166 alpha-2 code, e.g. ``"PL"``.
        subdivision: Optional subdivision code (empty string for none).
        year: Calendar year.

    Returns:
        A frozenset of :class:`datetime.date` — safe to cache.
    """
    kwargs: dict[str, Any] = {"years": year}
    if subdivision:
        kwargs["subdiv"] = subdivision
    return frozenset(holidays_lib.country_holidays(country_code, **kwargs).keys())


def _daterange(start: date, end: date) -> list[date]:
    """Return the inclusive list of dates from ``start`` to ``end``."""
    if end < start:
        return []
    span = (end - start).days
    return [start + timedelta(days=offset) for offset in range(span + 1)]


def is_working(calendar: Calendar, day: date) -> bool:
    """Return True iff ``day`` is a working day under ``calendar``.

    A day is working iff its weekday is set in the calendar's weekly
    pattern *and* it is not a holiday in the calendar's holiday source.
    """
    if not calendar.weekly_pattern.is_working_weekday(day.weekday()):
        return False
    hc = calendar.holiday_calendar
    return day not in _holidays_for_year(hc.country_code, hc.subdivision, day.year)


def working_days(calendar: Calendar, start: date, end: date) -> list[date]:
    """Return the sorted list of working days in ``[start, end]`` inclusive."""
    return [day for day in _daterange(start, end) if is_working(calendar, day)]


def free_days(calendar: Calendar, start: date, end: date) -> set[date]:
    """Return the set of non-working days in ``[start, end]`` inclusive."""
    return {day for day in _daterange(start, end) if not is_working(calendar, day)}


def working_days_count(calendar: Calendar, start: date, end: date) -> int:
    """Return the number of working days in ``[start, end]`` inclusive."""
    return sum(1 for day in _daterange(start, end) if is_working(calendar, day))


# ─── Person-scoped helpers ──────────────────────────────────────────────────


def calendar_on(person: Person, day: date) -> Calendar | None:
    """Return the :class:`Calendar` assigned to ``person`` on ``day``, or ``None``.

    Selects the :class:`~calendars.models.CalendarAssignment` whose
    ``start_date <= day`` and whose ``end_date`` is either ``NULL`` or
    ``>= day``. Returns ``None`` when no assignment covers ``day``.

    Assignments are guaranteed not to overlap by model validation, so at
    most one calendar applies per date.
    """
    from django.db.models import Q

    assignment = (
        person.calendar_assignments.filter(start_date__lte=day)
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=day))
        .select_related("calendar__weekly_pattern", "calendar__holiday_calendar")
        .first()
    )
    return assignment.calendar if assignment else None


def is_working_for(person: Person, day: date) -> bool | None:
    """Return whether ``day`` is a working day for ``person``, or ``None``.

    ``None`` means no calendar assignment covers ``day`` — the caller must
    decide the fallback (treat as working, treat as free, or raise).
    """
    calendar = calendar_on(person, day)
    if calendar is None:
        return None
    return is_working(calendar, day)


def working_days_for(person: Person, start: date, end: date) -> list[date]:
    """Return the working days in ``[start, end]`` under the person's calendars.

    Days not covered by any assignment are *excluded* from the result
    (interpreted as "unknown, not counted"). Callers that need a different
    fallback should use :func:`calendar_on` directly.
    """
    result: list[date] = []
    for day in _daterange(start, end):
        calendar = calendar_on(person, day)
        if calendar is not None and is_working(calendar, day):
            result.append(day)
    return result
