"""Companies models."""

from django.db import models


class Company(models.Model):
    """Company model."""

    identifier = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)

    def __str__(self):
        """Return the name of the company."""
        return self.name
