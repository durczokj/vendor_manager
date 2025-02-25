"""Forms for the people app."""

from django import forms

from .models import Person


class PersonForm(forms.ModelForm):
    """Form for creating and updating Person objects."""

    class Meta:
        """Meta class to define the model and fields to be used."""

        model = Person
        fields = ["id", "first_name", "last_name", "description", "location", "user"]
