"""FilterSets for the calendars app."""

from django_filters import rest_framework as filters

from calendars.models import Calendar, CalendarAssignment, HolidayCalendar, WeeklyPattern


class WeeklyPatternFilterSet(filters.FilterSet):
    """FilterSet for the WeeklyPattern model."""

    class Meta:
        """FilterSet metadata."""

        model = WeeklyPattern
        fields = ["name", "working_days"]


class HolidayCalendarFilterSet(filters.FilterSet):
    """FilterSet for the HolidayCalendar model."""

    class Meta:
        """FilterSet metadata."""

        model = HolidayCalendar
        fields = ["name", "country_code", "subdivision"]


class CalendarFilterSet(filters.FilterSet):
    """FilterSet for the Calendar model."""

    class Meta:
        """FilterSet metadata."""

        model = Calendar
        fields = ["name", "weekly_pattern", "holiday_calendar"]


class CalendarAssignmentFilterSet(filters.FilterSet):
    """FilterSet for the CalendarAssignment model."""

    class Meta:
        """FilterSet metadata."""

        model = CalendarAssignment
        fields = ["person", "calendar", "start_date", "end_date"]
