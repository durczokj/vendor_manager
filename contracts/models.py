"""Model for contracts."""

from django.db import models

from contracts.managers import ContractManager


class Contract(models.Model):
    """Model for contracts."""

    objects = ContractManager()

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    size = models.IntegerField()

    def __str__(self) -> str:
        """Return the name of the contract."""
        return self.name
