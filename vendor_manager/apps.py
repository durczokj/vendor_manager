"""App config for the ``vendor_manager`` project app."""

from __future__ import annotations

from typing import Any

from django.apps import AppConfig
from django.db.models.signals import post_migrate


def _ensure_role_groups(sender: Any, **kwargs: Any) -> None:
    """Create a Django ``Group`` for every role defined in :mod:`vendor_manager.roles`."""
    from django.contrib.auth.models import Group

    from vendor_manager.roles import Admin, Person, UndertakingManager

    for role_cls in (Person, UndertakingManager, Admin):
        Group.objects.get_or_create(name=role_cls.get_name())


class VendorManagerConfig(AppConfig):
    """Ensure role groups exist after every migrate."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "vendor_manager"

    def ready(self) -> None:
        """Connect the ``post_migrate`` signal that provisions role groups."""
        post_migrate.connect(_ensure_role_groups, sender=self)
