from django.db import models

class CostCenter(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)

class Undertaking(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    cost_center = models.ForeignKey(CostCenter, related_name='undertakings', on_delete=models.CASCADE)

    def __str__(self):
        return self.name