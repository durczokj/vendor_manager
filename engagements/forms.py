"""Forms for the engagements app."""

from django import forms

from .models import Engagement


class EngagementForm(forms.ModelForm):
    """Form for creating and updating engagements."""

    class Meta:
        """Meta class for EngagementForm."""

        model = Engagement
        fields = "__all__"
