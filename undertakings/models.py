"""Models for the undertakings app."""

from django.db import models


class CostCenter(models.Model):
    """Model for a cost center."""

    identifier = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)


class Undertaking(models.Model):
    """Model for an undertaking."""

    identifier = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    cost_center = models.ForeignKey(CostCenter, related_name="undertakings", on_delete=models.CASCADE)

    def __str__(self):
        """Return the name of the undertaking."""
        return self.name
