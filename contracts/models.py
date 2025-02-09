"""Model for contracts."""

from django.db import models


class Contract(models.Model):
    """Model for contracts."""

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    size = models.IntegerField()
