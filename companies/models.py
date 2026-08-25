"""Companies models."""

from django.db import models

from companies.managers import CompanyManager


class Company(models.Model):
    """Company model."""

    objects = CompanyManager()

    id = models.IntegerField(
        primary_key=True,
        help_text="Business-supplied company identifier (integer, immutable).",
    )
    name = models.CharField(
        max_length=255,
        help_text="Display name of the company (e.g. 'Acme Corp').",
    )
    email = models.EmailField(
        max_length=255,
        help_text="Primary billing / contact email for the company.",
    )

    def __str__(self) -> str:
        """Return the name of the company."""
        return self.name
