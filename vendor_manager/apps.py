"""App config for the ``vendor_manager`` project app."""

from __future__ import annotations

from typing import Any

from django.apps import AppConfig
from django.db.models.signals import post_migrate, post_save


def _ensure_role_groups(sender: Any, **kwargs: Any) -> None:
    """Create a Django ``Group`` for every role defined in :mod:`vendor_manager.roles`."""
    from django.contrib.auth.models import Group

    from vendor_manager.roles import Admin, Person, UndertakingManager

    for role_cls in (Person, UndertakingManager, Admin):
        Group.objects.get_or_create(name=role_cls.get_name())


def _sync_superuser_admin_role(sender: Any, instance: Any, **kwargs: Any) -> None:
    """Assign the RBAC ``admin`` role to every user with ``is_superuser=True``."""
    from rolepermissions.checkers import has_role
    from rolepermissions.roles import assign_role

    if getattr(instance, "is_superuser", False) and not has_role(instance, "admin"):
        assign_role(instance, "admin")


class VendorManagerConfig(AppConfig):
    """Ensure role groups exist after every migrate."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "vendor_manager"

    def ready(self) -> None:
        """Connect the ``post_migrate`` and ``post_save`` signals."""
        from django.contrib.auth.models import User

        post_migrate.connect(_ensure_role_groups, sender=self)
        post_save.connect(
            _sync_superuser_admin_role,
            sender=User,
            dispatch_uid="vendor_manager.sync_superuser_admin_role",
        )
