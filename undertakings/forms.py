"""Forms for the undertakings app."""

from django import forms

from .models import Undertaking


class UndertakingForm(forms.ModelForm):
    """Form for creating and updating undertakings."""

    class Meta:
        """Form for creating and updating undertakings."""

        model = Undertaking
        fields = "__all__"
