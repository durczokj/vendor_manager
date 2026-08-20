"""Models for leaves app."""

from typing import Any

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from leaves.managers import LeaveManager
from people.models import Person


class Leave(models.Model):
    """Model for leave requests."""

    objects = LeaveManager()

    person = models.ForeignKey(Person, related_name="leaves", on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    percentage = models.DecimalField(
        max_digits=3, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(1)]
    )

    def clean(self) -> None:
        """Validate that end_date is on or after start_date."""
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot be before start date."})

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Run clean before saving."""
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Return a string representation of the leave."""
        return f"{self.person} - from {self.start_date} to {self.end_date} – {self.percentage}%"
