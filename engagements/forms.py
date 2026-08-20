"""Forms for the engagements app."""

from django import forms

from engagements.services import update_engagement

from .models import Engagement, EngagementOrderVersionAssignment, EngagementUndertakingAssignment


class EngagementForm(forms.ModelForm):
    """Form for creating and updating engagements."""

    class Meta:
        """Meta class for EngagementForm."""

        model = Engagement
        fields = "__all__"

    def save(self, commit: bool = True) -> Engagement:
        """Save an engagement and apply service-level update behavior for edits."""
        engagement: Engagement = super().save(commit=False)

        if commit:
            if engagement.pk is None:
                engagement.save()
            else:
                update_engagement(engagement=engagement)
        return engagement


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
