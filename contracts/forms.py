"""Forms for contracts app."""

from django import forms

from .models import Contract


class ContractForm(forms.ModelForm):
    """Form for Contract model."""

    class Meta:
        """Meta class for ContractForm."""

        model = Contract
        fields = "__all__"
