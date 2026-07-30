"""Check if user is assigned to a person."""

from __future__ import annotations

import django.contrib.auth.models as mo
from django.contrib.auth.models import User
from rolepermissions.checkers import has_role

EXEMPTED_ROLES = ["admin"]


class NoPersonAssignedToUser(Exception):
    """Exception raised when user is not assigned to a person and is not exempted."""

    def __init__(self, user: User, exempted_roles: list[str]) -> None:
        """Store the offending user and the list of roles allowed to bypass this check."""
        message = f"User {user.username} is not assigned to any person.\nExempted roles: {exempted_roles}."
        super().__init__(message)


def check_user_person_assignment(user: User) -> None:
    """Check if user is assigned to a person.

    Args:
        user: The authenticated Django user to check.

    Raises:
        NoPersonAssignedToUser: When the user has no linked Person and does
            not hold an exempted role.
    """
    for role in EXEMPTED_ROLES:
        if has_role(user, role):
            return

    try:
        _ = user.person  # noqa: B018 — attribute access triggers RelatedObjectDoesNotExist
    except mo.User.person.RelatedObjectDoesNotExist as exc:
        raise NoPersonAssignedToUser(user, EXEMPTED_ROLES) from exc
