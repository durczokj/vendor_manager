"""DRF permission classes for the calendars app."""

from __future__ import annotations

from typing import Any

from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request
from rolepermissions.checkers import has_object_permission, has_permission
from rolepermissions.roles import get_user_roles

from calendars.models import CalendarAssignment


def _method_to_perm(method: str, model_name: str) -> str:
    """Map an HTTP method to the corresponding rolepermissions codename."""
    if method in SAFE_METHODS:
        return f"view_{model_name}"
    if method == "POST":
        return f"add_{model_name}"
    if method in {"PUT", "PATCH"}:
        return f"change_{model_name}"
    if method == "DELETE":
        return f"delete_{model_name}"
    return f"view_{model_name}"


class HasRolePermission(BasePermission):
    """Grant access to a viewset based on a per-model rolepermissions codename.

    The viewset must declare ``rp_model_name`` \u2014 the lowercase
    ``_meta.model_name`` used as the suffix of the ``{view,add,change,delete}_``
    permission codenames declared in :mod:`vendor_manager.roles`.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        """Return True iff the caller's role holds the mapped permission codename."""
        user = request.user
        if not getattr(user, "is_authenticated", False):
            return False
        if not get_user_roles(user):
            return False
        model_name = getattr(view, "rp_model_name", None)
        if not model_name:
            return False
        return bool(has_permission(user, _method_to_perm(request.method or "", model_name)))


class CanAccessAssignmentPerson(BasePermission):
    """Object-level check for :class:`CalendarAssignment` writes.

    Admins pass unconditionally (they hold every ``access_person`` scope by
    virtue of the ``access_person`` object checker). Undertaking Managers are
    restricted to assignments whose ``person`` they can access via the shared
    ``access_person`` object checker.

    Read requests bypass this check \u2014 list/detail scoping is handled at
    the queryset level.
    """

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        """Return True iff the user can access the target assignment's person."""
        if request.method in SAFE_METHODS:
            return True
        if not isinstance(obj, CalendarAssignment):
            return True
        return bool(has_object_permission("access_person", request.user, obj.person))
