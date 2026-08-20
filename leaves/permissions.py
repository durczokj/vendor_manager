"""Define permissions for leaves app."""

from typing import Any

from django.contrib.auth.models import User
from rolepermissions.permissions import register_object_checker

from leaves.models import Leave


@register_object_checker()
def access_leave(role: Any, user: User, leave: Leave) -> bool:
    """Check if user has access to the leave."""
    del role
    return type(leave).objects.accessible_to(user).filter(pk=leave.pk).exists()
