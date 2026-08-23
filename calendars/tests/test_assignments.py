"""Tests for calendars.models.CalendarAssignment."""

from __future__ import annotations

from datetime import date

import pytest
from django.core.exceptions import ValidationError

from calendars.tests.factories import CalendarAssignmentFactory, CalendarFactory
from people.tests.factories import PersonFactory


@pytest.mark.django_db
def test_end_before_start_rejected():
    """``end_date`` before ``start_date`` fails validation."""
    with pytest.raises(ValidationError):
        CalendarAssignmentFactory(
            start_date=date(2026, 6, 1),
            end_date=date(2026, 1, 1),
        )


@pytest.mark.django_db
def test_open_ended_assignment_allowed():
    """``end_date`` may be ``None``."""
    assignment = CalendarAssignmentFactory(start_date=date(2026, 1, 1), end_date=None)
    assert assignment.pk is not None


@pytest.mark.django_db
def test_non_overlapping_ranges_for_same_person_allowed():
    """Back-to-back assignments (touching only at boundary) are not permitted.

    Since the ranges are closed on both ends, ``2026-06-30`` and ``2026-06-30``
    would overlap. Use ``2026-07-01`` for the second range to avoid overlap.
    """
    person = PersonFactory()
    CalendarAssignmentFactory(
        person=person,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 6, 30),
    )
    later = CalendarAssignmentFactory(
        person=person,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 12, 31),
    )
    assert later.pk is not None


@pytest.mark.django_db
def test_overlapping_ranges_for_same_person_rejected():
    """Two overlapping closed ranges for the same person raise ValidationError."""
    person = PersonFactory()
    CalendarAssignmentFactory(
        person=person,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 6, 30),
    )
    with pytest.raises(ValidationError):
        CalendarAssignmentFactory(
            person=person,
            start_date=date(2026, 6, 15),
            end_date=date(2026, 12, 31),
        )


@pytest.mark.django_db
def test_overlap_with_open_ended_rejected():
    """A finite range that starts inside an open-ended existing range is rejected."""
    person = PersonFactory()
    CalendarAssignmentFactory(
        person=person,
        start_date=date(2026, 1, 1),
        end_date=None,
    )
    with pytest.raises(ValidationError):
        CalendarAssignmentFactory(
            person=person,
            start_date=date(2026, 6, 15),
            end_date=date(2026, 12, 31),
        )


@pytest.mark.django_db
def test_overlap_only_within_same_person():
    """Two people can have overlapping ranges independently."""
    person_a = PersonFactory(id="AAAAAA")
    person_b = PersonFactory(id="BBBBBB")
    calendar = CalendarFactory()
    CalendarAssignmentFactory(
        person=person_a,
        calendar=calendar,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )
    b_assignment = CalendarAssignmentFactory(
        person=person_b,
        calendar=calendar,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )
    assert b_assignment.pk is not None


@pytest.mark.django_db
def test_str_includes_person_and_dates():
    """``__str__`` shows the person id and the date range."""
    person = PersonFactory(id="P00042")
    calendar = CalendarFactory(name="cal")
    a = CalendarAssignmentFactory(
        person=person,
        calendar=calendar,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )
    assert "P00042" in str(a)
    assert "2026-01-01" in str(a)
    assert "2026-12-31" in str(a)
