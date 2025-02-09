from django.db import models
from django.contrib.auth.models import User


class Person(models.Model):
  id = models.CharField(primary_key=True, max_length=6)
  first_name = models.CharField(max_length=255)
  last_name = models.CharField(max_length=255)
  description = models.TextField(blank=False, null=True)
  location = models.CharField(max_length=255, blank=False, null=True)
  user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)

  def __str__(self):
    return f'{self.first_name} {self.last_name}'
  
  @property
  def active_engagements(self):
    return [e for e in self.engagements.all() if e.active]
  
  def get_assignments(self, active_only = False):
    assignmnents = []
    for e in self.engagements.all():
          for a in e.undertaking_assignments.all():
              assignmnents.append(a)
    return assignmnents

