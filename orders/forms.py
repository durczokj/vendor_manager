"""Forms for the engagements app."""

from django import forms

from contracts.models import Contract

from .models import Order, OrderVersion


class OrderForm(forms.ModelForm):
    """Form for creating and updating engagements."""

    class Meta:
        """Meta class for EngagementForm."""

        model = Order
        fields = "__all__"


class OrderVersionForm(forms.ModelForm):
    """Form for creating and updating engagements."""

    class Meta:
        """Meta class for EngagementForm."""

        model = OrderVersion
        fields = "__all__"


class CloneLatestVersionForm(forms.Form):
    """Form for cloning the latest version of an order with start and end dates."""

    start_date = forms.DateField(required=True, widget=forms.DateInput(attrs={"type": "text"}, format="%Y-%m-%d"))
    end_date = forms.DateField(required=True, widget=forms.DateInput(attrs={"type": "text"}, format="%Y-%m-%d"))
    copy_engagement_assignments = forms.BooleanField(required=True)
    contract = forms.ModelChoiceField(queryset=Contract.objects.all(), required=True)
