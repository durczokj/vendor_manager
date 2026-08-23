"""Tests for calendars app selectors."""

from __future__ import annotations

from datetime import date

import pytest

from calendars.models import ALL_WEEK_MASK, MON_FRI_MASK
from calendars.selectors import (
    _holidays_for_year,
    calendar_on,
    free_days,
    is_working,
    is_working_for,
    working_days,
    working_days_count,
    working_days_for,
)
from calendars.tests.factories import (
    CalendarAssignmentFactory,
    CalendarFactory,
    HolidayCalendarFactory,
    WeeklyPatternFactory,
)
from people.tests.factories import PersonFactory


@pytest.fixture
def pl_mon_fri_calendar(db):
    """Return a Poland Mon-Fri calendar."""
    pattern = WeeklyPatternFactory(name="Mon-Fri", working_days=MON_FRI_MASK)
    hc = HolidayCalendarFactory(name="PL", country_code="PL", subdivision="")
    return CalendarFactory(name="PL Mon-Fri", weekly_pattern=pattern, holiday_calendar=hc)


@pytest.mark.django_db
def test_is_working_true_for_regular_weekday(pl_mon_fri_calendar):
    """A regular weekday that isn't a Polish holiday is a working day."""
    # 2026-08-20 is a Thursday and not a Polish public holiday.
    assert is_working(pl_mon_fri_calendar, date(2026, 8, 20)) is True


@pytest.mark.django_db
def test_is_working_false_for_saturday(pl_mon_fri_calendar):
    """Saturdays are non-working under a Mon-Fri weekly pattern."""
    assert is_working(pl_mon_fri_calendar, date(2026, 8, 22)) is False


@pytest.mark.django_db
def test_is_working_false_for_polish_new_year(pl_mon_fri_calendar):
    """2026-01-01 (Thursday) is a Polish public holiday."""
    assert is_working(pl_mon_fri_calendar, date(2026, 1, 1)) is False


@pytest.mark.django_db
def test_working_days_and_free_days_partition_range(pl_mon_fri_calendar):
    """working_days ∪ free_days == all days in range, and they are disjoint."""
    start = date(2026, 1, 1)
    end = date(2026, 1, 31)
    working = set(working_days(pl_mon_fri_calendar, start, end))
    free = free_days(pl_mon_fri_calendar, start, end)
    total = 31
    assert working.isdisjoint(free)
    assert len(working) + len(free) == total


@pytest.mark.django_db
def test_working_days_count_matches_working_days_length(pl_mon_fri_calendar):
    """``working_days_count`` matches ``len(working_days(...))``."""
    start = date(2026, 3, 1)
    end = date(2026, 3, 31)
    assert working_days_count(pl_mon_fri_calendar, start, end) == len(working_days(pl_mon_fri_calendar, start, end))


@pytest.mark.django_db
def test_working_days_empty_when_end_before_start(pl_mon_fri_calendar):
    """Returns an empty list when end < start."""
    assert working_days(pl_mon_fri_calendar, date(2026, 6, 1), date(2026, 5, 31)) == []


@pytest.mark.django_db
def test_all_week_pattern_only_removes_holidays():
    """A 24/7 pattern only excludes holidays."""
    pattern = WeeklyPatternFactory(name="always", working_days=ALL_WEEK_MASK)
    hc = HolidayCalendarFactory(name="PL2", country_code="PL", subdivision="")
    cal = CalendarFactory(name="PL always", weekly_pattern=pattern, holiday_calendar=hc)
    start = date(2026, 1, 1)
    end = date(2026, 12, 31)
    total = (end - start).days + 1
    holidays_in_year = _holidays_for_year("PL", "", 2026)
    assert working_days_count(cal, start, end) == total - len(holidays_in_year)


def test_holidays_for_year_is_frozenset():
    """The cached holiday set is a ``frozenset`` of ``date`` objects."""
    result = _holidays_for_year("PL", "", 2025)
    assert isinstance(result, frozenset)
    assert all(isinstance(d, date) for d in result)


def test_holidays_for_year_supports_subdivision():
    """Subdivision-scoped holidays differ from country-wide."""
    tx = _holidays_for_year("US", "TX", 2025)
    us = _holidays_for_year("US", "", 2025)
    assert tx != us


# ─── Person-scoped selectors ────────────────────────────────────────────────


@pytest.mark.django_db
def test_calendar_on_returns_calendar_within_range(pl_mon_fri_calendar):
    """``calendar_on`` returns the calendar covering the given day."""
    person = PersonFactory()
    CalendarAssignmentFactory(
        person=person,
        calendar=pl_mon_fri_calendar,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )
    result = calendar_on(person, date(2026, 6, 15))
    assert result is not None
    assert result.pk == pl_mon_fri_calendar.pk


@pytest.mark.django_db
def test_calendar_on_returns_none_outside_range(pl_mon_fri_calendar):
    """``calendar_on`` returns None when no assignment covers the day."""
    person = PersonFactory()
    CalendarAssignmentFactory(
        person=person,
        calendar=pl_mon_fri_calendar,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 6, 30),
    )
    assert calendar_on(person, date(2026, 7, 1)) is None


@pytest.mark.django_db
def test_calendar_on_supports_open_ended(pl_mon_fri_calendar):
    """An open-ended assignment covers any date on or after ``start_date``."""
    person = PersonFactory()
    CalendarAssignmentFactory(
        person=person,
        calendar=pl_mon_fri_calendar,
        start_date=date(2026, 1, 1),
        end_date=None,
    )
    result = calendar_on(person, date(2099, 1, 1))
    assert result is not None
    assert result.pk == pl_mon_fri_calendar.pk


@pytest.mark.django_db
def test_calendar_on_switches_across_boundaries():
    """``calendar_on`` returns the right calendar on either side of a switch."""
    person = PersonFactory()
    cal_a = CalendarFactory(name="A")
    cal_b = CalendarFactory(name="B")
    CalendarAssignmentFactory(
        person=person,
        calendar=cal_a,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 6, 30),
    )
    CalendarAssignmentFactory(
        person=person,
        calendar=cal_b,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 12, 31),
    )
    on_jun_30 = calendar_on(person, date(2026, 6, 30))
    on_jul_1 = calendar_on(person, date(2026, 7, 1))
    assert on_jun_30 is not None
    assert on_jul_1 is not None
    assert on_jun_30.pk == cal_a.pk
    assert on_jul_1.pk == cal_b.pk


@pytest.mark.django_db
def test_is_working_for_returns_none_when_unassigned():
    """``is_working_for`` returns None if no calendar covers the day."""
    person = PersonFactory()
    assert is_working_for(person, date(2026, 6, 15)) is None


@pytest.mark.django_db
def test_working_days_for_skips_unassigned_days(pl_mon_fri_calendar):
    """``working_days_for`` excludes days not covered by any assignment."""
    person = PersonFactory()
    CalendarAssignmentFactory(
        person=person,
        calendar=pl_mon_fri_calendar,
        start_date=date(2026, 3, 2),  # Monday
        end_date=date(2026, 3, 6),  # Friday
    )
    result = working_days_for(person, date(2026, 3, 1), date(2026, 3, 31))
    # Only the five weekdays in the assigned window (none are Polish holidays).
    assert result == [
        date(2026, 3, 2),
        date(2026, 3, 3),
        date(2026, 3, 4),
        date(2026, 3, 5),
        date(2026, 3, 6),
    ]
