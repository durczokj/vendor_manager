"""Companies models."""

from django.db import models

from companies.managers import CompanyManager


class Company(models.Model):
    """Company model."""

    objects = CompanyManager()

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)

    def __str__(self) -> str:
        """Return the name of the company."""
        return self.name
