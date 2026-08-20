"""Model for a person."""

from typing import TYPE_CHECKING

from django.contrib.auth.models import User
from django.db import models

from people.managers import PersonManager

if TYPE_CHECKING:
    from engagements.models import Engagement, EngagementUndertakingAssignment


class Person(models.Model):
    """Model for a person."""

    objects = PersonManager()

    id = models.CharField(primary_key=True, max_length=6)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=False, default="")
    location = models.CharField(max_length=255, blank=True, null=False, default="")
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)

    @property
    def name(self) -> str:
        """Return the full name of the person."""
        return f"{self.first_name} {self.last_name}"

    def __str__(self) -> str:
        """Return the full name of the person."""
        return f"{self.id} \u2013 {self.name}"

    @property
    def active_engagements(self) -> list["Engagement"]:
        """Return all active engagements for this person."""
        return [e for e in self.engagements.all() if e.active()]

    def get_assignments(self) -> list["EngagementUndertakingAssignment"]:
        """Return all assignments for this person."""
        assignments = []
        for eng in self.engagements.all():
            for ass in eng.undertaking_assignments.all():
                assignments.append(ass)
        return assignments
