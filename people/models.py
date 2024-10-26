from django.db import models

class Person(models.Model):
  id = models.CharField(primary_key=True, max_length=6)
  first_name = models.CharField(max_length=255)
  last_name = models.CharField(max_length=255)
  description = models.TextField(blank=False, null=True)
  location = models.CharField(max_length=255, blank=False, null=True)

  def __str__(self):
    return f'{self.first_name} {self.last_name}'