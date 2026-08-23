"""Tests for calendars app models."""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError

from calendars.models import ALL_WEEK_MASK, MON_FRI_MASK, WeeklyPattern
from calendars.tests.factories import (
    CalendarFactory,
    HolidayCalendarFactory,
    WeeklyPatternFactory,
)


@pytest.mark.django_db
def test_weekly_pattern_is_working_weekday_mon_fri():
    """Mon–Fri pattern reports Mon–Fri as working and Sat–Sun as free."""
    pattern = WeeklyPatternFactory(working_days=MON_FRI_MASK)
    working = [pattern.is_working_weekday(day) for day in range(7)]
    assert working == [True, True, True, True, True, False, False]


@pytest.mark.django_db
def test_weekly_pattern_all_week_mask():
    """A 24/7 pattern reports every weekday as working."""
    pattern = WeeklyPatternFactory(working_days=ALL_WEEK_MASK)
    assert all(pattern.is_working_weekday(day) for day in range(7))


def test_weekly_pattern_is_working_weekday_rejects_out_of_range():
    """Values outside [0, 6] raise ``ValueError``."""
    pattern = WeeklyPattern(name="x", working_days=MON_FRI_MASK)
    with pytest.raises(ValueError, match="weekday must be in"):
        pattern.is_working_weekday(7)


@pytest.mark.django_db
def test_weekly_pattern_full_clean_rejects_out_of_range_mask():
    """``working_days`` above 127 fails model validation."""
    pattern = WeeklyPatternFactory.build(name="bad", working_days=128)
    with pytest.raises(ValidationError):
        pattern.full_clean()


@pytest.mark.django_db
def test_calendar_str_uses_name():
    """``__str__`` returns the calendar name."""
    calendar = CalendarFactory(name="PL Mon-Fri")
    assert str(calendar) == "PL Mon-Fri"


@pytest.mark.django_db
def test_holiday_calendar_str_uses_name():
    """``__str__`` returns the holiday calendar name."""
    hc = HolidayCalendarFactory(name="Poland public")
    assert str(hc) == "Poland public"
