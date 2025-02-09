"""Model for a person."""

from django.contrib.auth.models import User
from django.db import models


class Person(models.Model):
    """Model for a person."""

    id = models.CharField(primary_key=True, max_length=6)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    description = models.TextField(blank=False, null=True)
    location = models.CharField(max_length=255, blank=False, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        """Return the full name of the person."""
        return f"{self.first_name} {self.last_name}"

    @property
    def active_engagements(self):
        """Return all active engagements for this person."""
        return [e for e in self.engagements.all() if e.active]

    def get_assignments(self, active_only=False):
        """Return all assignments for this person."""
        assignmnents = []
        for eng in self.engagements.all():
            for ass in eng.undertaking_assignments.all():
                assignmnents.append(ass)
        return assignmnents
