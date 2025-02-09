"""Models for leaves app."""

from django.db import models

from people.models import Person


class Leave(models.Model):
    """Model for leave requests."""

    person = models.ForeignKey(Person, related_name="leaves", on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    percentage = models.DecimalField(max_digits=3, decimal_places=2)
