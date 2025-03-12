"""Forms for the engagements app."""

from django import forms

from .models import Engagement, EngagementOrderVersionAssignment, EngagementUndertakingAssignment


class EngagementForm(forms.ModelForm):
    """Form for creating and updating engagements."""

    class Meta:
        """Meta class for EngagementForm."""

        model = Engagement
        fields = "__all__"


class EngagementUndertakingAssignmentForm(forms.ModelForm):
    """Form for creating and updating engagements."""

    class Meta:
        """Meta class for EngagementForm."""

        model = EngagementUndertakingAssignment
        fields = "__all__"


class EngagementOrderVersionAssignmentForm(forms.ModelForm):
    """Form for creating and updating engagements."""

    class Meta:
        """Meta class for EngagementForm."""

        model = EngagementOrderVersionAssignment
        fields = "__all__"
