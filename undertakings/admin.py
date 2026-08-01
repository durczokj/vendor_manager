"""This module registers the Undertaking model with the Django admin site."""

from django.contrib import admin

from .models import CostCenter, Undertaking

admin.site.register(Undertaking)
admin.site.register(CostCenter)
