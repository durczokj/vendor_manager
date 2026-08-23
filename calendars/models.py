"""Models for the calendars app."""

from __future__ import annotations

from datetime import date
from typing import Any

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from calendars.managers import CalendarAssignmentManager

# Bit positions for weekdays, matching ``datetime.date.weekday()``.
MONDAY = 0
TUESDAY = 1
WEDNESDAY = 2
THURSDAY = 3
FRIDAY = 4
SATURDAY = 5
SUNDAY = 6

# Convenience constants used by data migrations / defaults.
MON_FRI_MASK = (1 << MONDAY) | (1 << TUESDAY) | (1 << WEDNESDAY) | (1 << THURSDAY) | (1 << FRIDAY)  # 0b0011111 == 31
ALL_WEEK_MASK = (1 << 7) - 1  # 0b1111111 == 127


class WeeklyPattern(models.Model):
    """A recurring weekly working-day pattern (Monday-based bitmask).

    ``working_days`` is a 7-bit mask: bit *k* set means weekday *k* is a
    working day, where *k* matches :meth:`datetime.date.weekday` (Monday=0,
    Sunday=6).
    """

    name = models.CharField(max_length=100, unique=True)
    working_days = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(ALL_WEEK_MASK)],
        help_text="7-bit mask; bit 0=Mon … bit 6=Sun. E.g. Mon-Fri = 31.",
    )

    class Meta:
        """Model metadata."""

        ordering = ["name"]

    def __str__(self) -> str:
        """Return the pattern name."""
        return self.name

    def is_working_weekday(self, weekday: int) -> bool:
        """Return True iff ``weekday`` (0=Mon … 6=Sun) is a working day."""
        if not 0 <= weekday <= 6:
            raise ValueError(f"weekday must be in [0, 6], got {weekday!r}")
        return bool(self.working_days & (1 << weekday))


class HolidayCalendar(models.Model):
    """A public-holiday source, resolved dynamically via the ``holidays`` library.

    ``country_code`` must be an ISO-3166 alpha-2 code supported by
    ``python-holidays``. ``subdivision`` is optional (e.g. US state
    ``"TX"``); leave empty for country-wide holidays.
    """

    name = models.CharField(max_length=100, unique=True)
    country_code = models.CharField(max_length=2)
    subdivision = models.CharField(max_length=10, blank=True, default="")

    class Meta:
        """Model metadata."""

        ordering = ["name"]

    def __str__(self) -> str:
        """Return the calendar name."""
        return self.name


class Calendar(models.Model):
    """A working calendar assignable to a :class:`people.models.Person`.

    A ``Calendar`` bundles one :class:`WeeklyPattern` (recurring weekly off
    days) with one :class:`HolidayCalendar` (special free days). The set of
    free/working days for any date range is computed on demand from these
    two components — no per-day rows are materialized.
    """

    name = models.CharField(max_length=100, unique=True)
    weekly_pattern = models.ForeignKey(WeeklyPattern, on_delete=models.PROTECT, related_name="calendars")
    holiday_calendar = models.ForeignKey(HolidayCalendar, on_delete=models.PROTECT, related_name="calendars")

    class Meta:
        """Model metadata."""

        ordering = ["name"]

    def __str__(self) -> str:
        """Return the calendar name."""
        return self.name


class CalendarAssignment(models.Model):
    """Time-scoped assignment of a :class:`Calendar` to a :class:`~people.models.Person`.

    A person may have multiple, non-overlapping assignments over their
    lifetime (e.g. Poland Mon-Fri until a relocation, then Germany Mon-Fri).
    ``end_date`` may be ``NULL`` to represent an open-ended assignment
    (currently in effect with no scheduled end).
    """

    person = models.ForeignKey(
        "people.Person",
        on_delete=models.CASCADE,
        related_name="calendar_assignments",
    )
    calendar = models.ForeignKey(
        Calendar,
        on_delete=models.PROTECT,
        related_name="person_assignments",
    )
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    objects = CalendarAssignmentManager()

    class Meta:
        """Model metadata."""

        ordering = ["person_id", "start_date"]

    def __str__(self) -> str:
        """Return a human-readable representation."""
        end = self.end_date.isoformat() if self.end_date else "…"
        return f"{self.person_id}: {self.calendar} [{self.start_date} – {end}]"

    def clean(self) -> None:
        """Validate date range and non-overlap with other assignments."""
        super().clean()
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValidationError({"end_date": "end_date cannot be before start_date."})

        # Overlap check against other assignments of the same person.
        # Two ranges [a, b] and [c, d] overlap iff a <= d and c <= b, with
        # None end_dates treated as +infinity.
        other = CalendarAssignment.objects.filter(person_id=self.person_id)
        if self.pk is not None:
            other = other.exclude(pk=self.pk)
        for existing in other:
            if _ranges_overlap(self.start_date, self.end_date, existing.start_date, existing.end_date):
                raise ValidationError(
                    {
                        "start_date": (
                            f"Overlaps with assignment {existing.pk} "
                            f"({existing.start_date} – {existing.end_date or '…'})."
                        )
                    }
                )

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Run ``full_clean`` before saving."""
        self.full_clean()
        super().save(*args, **kwargs)


def _ranges_overlap(a_start: date, a_end: date | None, b_start: date, b_end: date | None) -> bool:
    """Return True iff closed date ranges ``[a_start, a_end]`` and ``[b_start, b_end]`` overlap.

    ``None`` end values are treated as ``+infinity``.
    """
    if a_end is None and b_end is None:
        return True
    if a_end is None:
        assert b_end is not None
        return a_start <= b_end
    if b_end is None:
        return b_start <= a_end
    return a_start <= b_end and b_start <= a_end
