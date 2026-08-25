"""Models for the undertakings app."""

from django.db import models

from undertakings.managers import CostCenterManager, UndertakingManager


class CostCenter(models.Model):
    """Model for a cost center."""

    objects = CostCenterManager()

    id = models.IntegerField(
        primary_key=True,
        help_text="Business-supplied cost-center identifier (integer, immutable).",
    )
    name = models.CharField(
        max_length=255,
        help_text="Display name of the cost center.",
    )

    def __str__(self) -> str:
        """Return the name of the cost center."""
        return self.name


class Undertaking(models.Model):
    """Model for an undertaking."""

    objects = UndertakingManager()

    id = models.IntegerField(
        primary_key=True,
        help_text="Business-supplied undertaking identifier (integer, immutable).",
    )
    name = models.CharField(
        max_length=255,
        help_text="Display name of the undertaking (project / workstream).",
    )
    cost_center = models.ForeignKey(
        CostCenter,
        related_name="undertakings",
        on_delete=models.CASCADE,
        help_text="Cost center this undertaking rolls up to.",
    )
    manager = models.ForeignKey(
        "people.Person",
        related_name="managed_undertakings",
        on_delete=models.CASCADE,
        help_text="Person accountable for this undertaking (the Undertaking Manager).",
    )

    def __str__(self) -> str:
        """Return the name of the undertaking."""
        return self.name
