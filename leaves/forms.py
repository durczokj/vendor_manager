"""Forms for managing leave requests."""

from django import forms
from rolepermissions.checkers import has_object_permission

from people.models import Person

from .models import Leave


class LeaveForm(forms.ModelForm):
    """Form for creating and updating leave requests."""

    class Meta:
        """Meta options for LeaveForm."""

        model = Leave
        fields = ["person", "start_date", "end_date", "percentage"]

    def __init__(self, *args, **kwargs):
        """Initialize the form with a user to filter the person queryset."""
        user = kwargs.pop("user", None)
        super(LeaveForm, self).__init__(*args, **kwargs)
        if user:
            self.fields["person"].queryset = Person.objects.filter(
                id__in=[
                    person.id for person in Person.objects.all() if has_object_permission("access_person", user, person)
                ]
            )
