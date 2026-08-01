"""Models for the undertakings app."""

from django.db import models

from undertakings.managers import CostCenterManager, UndertakingManager


class CostCenter(models.Model):
    """Model for a cost center."""

    objects = CostCenterManager()

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        """Return the name of the cost center."""
        return self.name


class Undertaking(models.Model):
    """Model for an undertaking."""

    objects = UndertakingManager()

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    cost_center = models.ForeignKey(CostCenter, related_name="undertakings", on_delete=models.CASCADE)
    manager = models.ForeignKey("people.Person", related_name="managed_undertakings", on_delete=models.CASCADE)

    def __str__(self):
        """Return the name of the undertaking."""
        return self.name
