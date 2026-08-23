"""Admin registrations for the calendars app."""

from django.contrib import admin

from .models import Calendar, CalendarAssignment, HolidayCalendar, WeeklyPattern


@admin.register(WeeklyPattern)
class WeeklyPatternAdmin(admin.ModelAdmin):  # type: ignore[type-arg]  # ModelAdmin generic is type-only, see repo memory
    list_display = ("name", "working_days")
    search_fields = ("name",)


@admin.register(HolidayCalendar)
class HolidayCalendarAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("name", "country_code", "subdivision")
    search_fields = ("name", "country_code", "subdivision")
    list_filter = ("country_code",)


@admin.register(Calendar)
class CalendarAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("name", "weekly_pattern", "holiday_calendar")
    search_fields = ("name",)
    list_select_related = ("weekly_pattern", "holiday_calendar")


@admin.register(CalendarAssignment)
class CalendarAssignmentAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("person", "calendar", "start_date", "end_date")
    search_fields = ("person__id", "person__first_name", "person__last_name", "calendar__name")
    list_filter = ("calendar",)
    list_select_related = ("person", "calendar")
