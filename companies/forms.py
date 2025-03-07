"""Forms for the companies app."""

from django import forms

from .models import Company


class CompanyForm(forms.ModelForm):
    """Form for creating a company."""

    class Meta:
        """Meta class for CompanyForm."""

        model = Company
        fields = "__all__"
