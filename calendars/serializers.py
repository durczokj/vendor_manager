"""Serializers for the calendars app."""

from rest_framework import serializers

from calendars.models import Calendar, CalendarAssignment, HolidayCalendar, WeeklyPattern


class WeeklyPatternSerializer(serializers.ModelSerializer[WeeklyPattern]):
    """Serialize WeeklyPattern rows for API operations."""

    class Meta:
        """Model serializer metadata."""

        model = WeeklyPattern
        fields = ["id", "name", "working_days"]


class HolidayCalendarSerializer(serializers.ModelSerializer[HolidayCalendar]):
    """Serialize HolidayCalendar rows for API operations."""

    class Meta:
        """Model serializer metadata."""

        model = HolidayCalendar
        fields = ["id", "name", "country_code", "subdivision"]


class CalendarSerializer(serializers.ModelSerializer[Calendar]):
    """Serialize Calendar rows for API operations."""

    class Meta:
        """Model serializer metadata."""

        model = Calendar
        fields = ["id", "name", "weekly_pattern", "holiday_calendar"]


class CalendarAssignmentSerializer(serializers.ModelSerializer[CalendarAssignment]):
    """Serialize CalendarAssignment rows for API operations."""

    class Meta:
        """Model serializer metadata."""

        model = CalendarAssignment
        fields = ["id", "person", "calendar", "start_date", "end_date"]
