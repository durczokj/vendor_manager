"""Model for contracts."""

from django.db import models

from contracts.managers import ContractManager


class Contract(models.Model):
    """Model for contracts."""

    objects = ContractManager()

    id = models.IntegerField(
        primary_key=True,
        help_text="Business-supplied contract identifier (integer, immutable).",
    )
    name = models.CharField(
        max_length=255,
        help_text="Display name of the contract (typically the contract reference).",
    )
    status = models.CharField(
        max_length=50,
        help_text="Free-form contract status label (e.g. 'active', 'closed', 'draft').",
    )
    size = models.IntegerField(
        help_text="Contracted volume in whole units (semantics defined by the contract).",
    )

    def __str__(self) -> str:
        """Return the name of the contract."""
        return self.name
