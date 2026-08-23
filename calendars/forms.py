"""Forms for the calendars app UI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django import forms

from .models import CalendarAssignment

if TYPE_CHECKING:
    _CalendarAssignmentModelForm = forms.ModelForm[CalendarAssignment]
else:
    _CalendarAssignmentModelForm = forms.ModelForm


class CalendarAssignmentForm(_CalendarAssignmentModelForm):
    """Form for creating and editing a :class:`CalendarAssignment`."""

    class Meta:
        """Meta options for :class:`CalendarAssignmentForm`."""

        model = CalendarAssignment
        fields = ("person", "calendar", "start_date", "end_date")
