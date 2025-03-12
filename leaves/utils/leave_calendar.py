"""Custom HTML calendar for displaying leaves."""

import calendar
from datetime import datetime

from django.utils.safestring import mark_safe


class LeaveCalendar(calendar.HTMLCalendar):
    """Custom HTML calendar for displaying leaves."""

    def __init__(self, year, month, leaves):
        """Initialize the calendar with the year, month, and leaves."""
        super().__init__()
        self.year = year
        self.month = month
        self.leaves = leaves
        self.colors = self.assign_colors()

    @staticmethod
    def to_html(leave):
        """Convert a leave object to an HTML string."""
        person_html = str(leave.person).replace("\u2013", "&ndash;")
        percentage_html = f"({leave.percentage})"
        return f"<div>{person_html} {percentage_html}</div>"

    def assign_colors(self):
        """Assign a unique color to each person."""
        unique_people = {leave.person.name for leave in self.leaves}
        colors = {}
        color_palette = [
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
        for i, person in enumerate(unique_people):
            colors[person] = color_palette[i % len(color_palette)]
        return colors

    def formatday(self, day, weekday):
        """Format a day as a table cell."""
        if day == 0:
            return '<td class="noday" style="border: 1px solid black;">&nbsp;</td>'  # Empty cell

        day = datetime(year=self.year, month=self.month, day=day).date()
        leave_entries = [leave for leave in self.leaves if leave.start_date <= day <= leave.end_date]

        leave_html = "".join(
            f'<div style="background-color: {self.colors[leave.person.name]}; padding: 2px; margin: 2px;">'
            f"{self.to_html(leave)}</div>"
            for leave in leave_entries
        )

        return (
            f'<td class="{self.cssclasses[weekday]}" '
            'style="border: 1px solid black; vertical-align: top;">'
            f"<b>{day}</b><br>{leave_html}</td>"
        )

    def formatmonth(self, withyear=True):
        """Create HTML table for a month."""
        return mark_safe(
            f"""
            <style>
                table.calendar {{
                    border-collapse: collapse;
                    width: 100%;
                }}
                table.calendar th, table.calendar td {{
                    border: 1px solid black;
                    padding: 4px;
                    text-align: center;
                }}
                table.calendar th {{
                    background-color: #f2f2f2;
                }}
            </style>
            <table class="calendar">
                {super().formatmonth(self.year, self.month, withyear)}
            </table>
        """
        )
