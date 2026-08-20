"""Project-level Django admin customizations.

Overrides the built-in User admin so that adding a user to one of the
role groups (``person``, ``undertaking_manager``, ``admin``) via the
standard *Groups* widget automatically grants the matching django-role-
permissions permissions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Permission, User
from django.http import HttpRequest
from rolepermissions.checkers import has_role
from rolepermissions.roles import AbstractUserRole

from vendor_manager.roles import Admin, Person, UndertakingManager

if TYPE_CHECKING:
    _UserAdminBase = DjangoUserAdmin[User]
else:
    _UserAdminBase = DjangoUserAdmin

ROLE_CLASSES: list[type[AbstractUserRole]] = [Person, UndertakingManager, Admin]
ROLE_LABELS = {
    Person.get_name(): "Person",
    UndertakingManager.get_name(): "Undertaking Manager",
    Admin.get_name(): "Admin",
}


def _sync_role_permissions(user: User) -> None:
    """Align ``user.user_permissions`` with the role groups the user belongs to."""
    role_perm_ids: set[int] = set()
    for role_cls in ROLE_CLASSES:
        for perm in role_cls.get_default_true_permissions():
            role_perm_ids.add(perm.pk)
    if role_perm_ids:
        user.user_permissions.remove(*Permission.objects.filter(pk__in=role_perm_ids))
    user_group_names = set(user.groups.values_list("name", flat=True))
    for role_cls in ROLE_CLASSES:
        if role_cls.get_name() in user_group_names:
            user.user_permissions.add(*role_cls.get_default_true_permissions())


class UserAdminWithRole(_UserAdminBase):
    """User admin that syncs role permissions from group membership on save."""

    def get_list_display(self, request: HttpRequest) -> list[Any]:
        """Add a Role column to the changelist."""
        return list(super().get_list_display(request)) + ["role_display"]

    @admin.display(description="Role")
    def role_display(self, obj: User) -> str:
        """Return the human-readable role name based on group membership."""
        for value, label in ROLE_LABELS.items():
            if has_role(obj, value):
                return label
        return "—"

    def save_related(self, request: HttpRequest, form: Any, formsets: Any, change: bool) -> None:
        """After groups m2m is saved, resync user_permissions from role groups."""
        super().save_related(request, form, formsets, change)
        _sync_role_permissions(form.instance)


admin.site.unregister(User)
admin.site.register(User, UserAdminWithRole)
