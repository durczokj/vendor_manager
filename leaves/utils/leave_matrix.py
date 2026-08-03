"""HTML matrix view for leaves: rows are people, columns are days of month."""

from __future__ import annotations

import calendar
from collections.abc import Iterable
from datetime import date

from django.utils.safestring import SafeString, mark_safe

_COLOR_PALETTE = [
    "#D2691E",
    "#FFB6C1",
    "#ADD8E6",
    "#90EE90",
    "#FFD700",
    "#FFA07A",
    "#20B2AA",
    "#9370DB",
    "#FF6347",
    "#4682B4",
]


class LeaveMatrix:
    """Render an HTML table of leaves with people as rows and days as columns.

    A cell is shaded if the person is on leave that day; the label shows the
    leave percentage. Empty cells mean the person is at work that day.
    """

    def __init__(self, year: int, month: int, leaves: Iterable[object]) -> None:
        """Initialize with the target month and the leaves overlapping it."""
        self.year = year
        self.month = month
        self.leaves = list(leaves)
        self.days_in_month = calendar.monthrange(year, month)[1]
        self.colors = self._assign_colors()

    def _assign_colors(self) -> dict[str, str]:
        unique_people = {str(leave.person) for leave in self.leaves}  # type: ignore[attr-defined]
        return {person: _COLOR_PALETTE[i % len(_COLOR_PALETTE)] for i, person in enumerate(sorted(unique_people))}

    def _rows(self) -> dict[str, list[object | None]]:
        """Group leaves per person, one slot per day of month."""
        rows: dict[str, list[object | None]] = {}
        for leave in self.leaves:
            key = str(leave.person)  # type: ignore[attr-defined]
            if key not in rows:
                rows[key] = [None] * self.days_in_month
            for day_number in range(1, self.days_in_month + 1):
                current = date(self.year, self.month, day_number)
                if leave.start_date <= current <= leave.end_date:  # type: ignore[attr-defined]
                    rows[key][day_number - 1] = leave
        return dict(sorted(rows.items()))

    def render(self) -> SafeString:
        """Return the matrix as safe HTML."""
        rows = self._rows()
        header_cells = "".join(f"<th>{day}</th>" for day in range(1, self.days_in_month + 1))

        body_rows = []
        for person, day_cells in rows.items():
            color = self.colors.get(person, "#EEEEEE")
            person_label = person.replace("\u2013", "&ndash;")
            cell_html_parts = []
            for leave in day_cells:
                if leave is None:
                    cell_html_parts.append("<td></td>")
                else:
                    pct = leave.percentage  # type: ignore[attr-defined]
                    cell_html_parts.append(f'<td style="background-color: {color}; text-align: center;">{pct}</td>')
            body_rows.append(f'<tr><th style="text-align: left;">{person_label}</th>{"".join(cell_html_parts)}</tr>')

        if not body_rows:
            body_rows.append(
                f'<tr><td colspan="{self.days_in_month + 1}" style="text-align: center; padding: 12px;">'
                "No leaves in this period.</td></tr>"
            )

        return mark_safe(
            f"""
            <style>
                table.leave-matrix {{
                    border-collapse: collapse;
                    width: 100%;
                    font-size: 0.9em;
                }}
                table.leave-matrix th, table.leave-matrix td {{
                    border: 1px solid #ccc;
                    padding: 3px 4px;
                }}
                table.leave-matrix thead th {{
                    background-color: #f2f2f2;
                    text-align: center;
                }}
            </style>
            <table class="leave-matrix">
                <thead>
                    <tr><th style="text-align: left;">Person</th>{header_cells}</tr>
                </thead>
                <tbody>
                    {"".join(body_rows)}
                </tbody>
            </table>
            """
        )
