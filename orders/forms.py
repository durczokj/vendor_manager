"""Forms for the engagements app."""

from django import forms

from .models import Order


class OrderForm(forms.ModelForm):
    """Form for creating and updating engagements."""

    class Meta:
        """Meta class for EngagementForm."""

        model = Order
        fields = "__all__"
