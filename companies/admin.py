"""This module registers the Company model with the Django admin site."""

from django.contrib import admin

from .models import Company

# Register your models here.
admin.site.register(Company)
