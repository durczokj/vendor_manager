"""This module registers the Undertaking model with the Django admin site."""

from django.contrib import admin

from .models import Undertaking

# Register your models here.
admin.site.register(Undertaking)
