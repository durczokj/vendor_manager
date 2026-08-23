"""HTML matrix view for leaves: rows are people, columns are days of month."""

from __future__ import annotations

import calendar
import html
from collections.abc import Iterable
from datetime import date
from typing import Any, Protocol

from django.utils.safestring import SafeString, mark_safe

from calendars.selectors import is_working_for


class _LeaveLike(Protocol):
    """Minimal duck-typed interface used by the matrix renderer."""

    person: Any
    start_date: date
    end_date: date
    percentage: Any


def _shade_for(percentage: float) -> str:
    """Return an ``rgba()`` fill for a given leave percentage.

    Uses a single hue and scales opacity linearly with percentage so that a
    100% day is a saturated cell and a 25% day is faint. Percentages outside
    [0, 1] are clamped.
    """
    pct = max(0.0, min(1.0, float(percentage)))
    alpha = 0.20 + 0.70 * pct
    return f"rgba(52, 152, 219, {alpha:.2f})"


# Fill applied to days that the person's assigned Calendar marks as free
# (weekend under the weekly pattern, or a public holiday).
_FREE_DAY_FILL = "rgba(231, 76, 60, 0.35)"


def _is_free_day(person: Any, day: date) -> bool:
    """Return True iff ``day`` is a non-working day under the person's calendar."""
    if not hasattr(person, "calendar_assignments"):
        return False
    return is_working_for(person, day) is False


class LeaveMatrix:
    """Render an HTML table of leaves with people as rows and days as columns.

    A cell is shaded blue if the person is on leave that day; the shade
    intensity is proportional to the leave percentage. A cell is shaded red
    when the person's assigned :class:`~calendars.models.Calendar` marks the
    day as free (weekly non-working day or public holiday). Leaves take
    precedence over free-day shading. If ``people`` is provided, every one
    of them gets a row (even with no leaves that month); otherwise only
    people with at least one overlapping leave are shown.
    """

    def __init__(
        self,
        year: int,
        month: int,
        leaves: Iterable[_LeaveLike],
        people: Iterable[Any] | None = None,
    ) -> None:
        """Initialize with the target month, overlapping leaves, and (optionally) all people to show."""
        self.year = year
        self.month = month
        self.leaves = list(leaves)
        self.people = list(people) if people is not None else None
        self.days_in_month = calendar.monthrange(year, month)[1]

    def _rows(self) -> dict[str, tuple[Any, list[_LeaveLike | None]]]:
        """Group leaves per person, one slot per day of month.

        The value is a ``(person, cells)`` tuple so the renderer can query
        the person's calendar for free-day shading without another lookup.
        """
        rows: dict[str, tuple[Any, list[_LeaveLike | None]]] = {}
        if self.people is not None:
            for person in self.people:
                rows[str(person)] = (person, [None] * self.days_in_month)
        for leave in self.leaves:
            key = str(leave.person)
            if key not in rows:
                rows[key] = (leave.person, [None] * self.days_in_month)
            person_obj, day_cells = rows[key]
            for day_number in range(1, self.days_in_month + 1):
                current = date(self.year, self.month, day_number)
                if leave.start_date <= current <= leave.end_date:
                    day_cells[day_number - 1] = leave
        return dict(sorted(rows.items()))

    def render(self) -> SafeString:
        """Return the matrix as safe HTML.

        Relies on the global table styles for the header/border look and on
        the template's ``.leave-matrix`` scoped CSS for row striping.
        """
        rows = self._rows()
        header_cells = "".join(f"<th>{day}</th>" for day in range(1, self.days_in_month + 1))

        body_rows: list[str] = []
        for person_label, (person_obj, day_cells) in rows.items():
            cell_html_parts: list[str] = []
            for day_index, leave in enumerate(day_cells, start=1):
                current = date(self.year, self.month, day_index)
                if leave is not None:
                    pct = float(leave.percentage)
                    fill = _shade_for(pct)
                    cell_html_parts.append(f'<td class="leave-cell" style="background-color: {fill};">{pct:.2f}</td>')
                elif _is_free_day(person_obj, current):
                    cell_html_parts.append(
                        f'<td class="leave-cell free-day" style="background-color: {_FREE_DAY_FILL};"></td>'
                    )
                else:
                    cell_html_parts.append('<td class="leave-cell"></td>')
            person_escaped = html.escape(person_label, quote=True)
            body_rows.append(
                f'<tr><th scope="row" title="{person_escaped}">{person_escaped}</th>{"".join(cell_html_parts)}</tr>'
            )

        if not body_rows:
            body_rows.append(
                f'<tr><td colspan="{self.days_in_month + 1}" style="text-align: center; padding: 12px;">'
                "No leaves in this period.</td></tr>"
            )

        return mark_safe(
            f'<table class="leave-matrix">'
            f"<thead><tr><th>Person</th>{header_cells}</tr></thead>"
            f"<tbody>{''.join(body_rows)}</tbody>"
            f"</table>"
        )
