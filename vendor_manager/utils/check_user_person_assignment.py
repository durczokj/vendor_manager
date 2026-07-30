"""Check if user is assigned to a person."""

import django.contrib.auth.models as mo
from rolepermissions.checkers import has_role

EXEMPTED_ROLES = ["admin"]


class NoPersonAssignedToUser(Exception):
    """Exception raised when user is not assigned to a person and is not exempted."""

    def __init__(self, user, exempted_roles):
        """Store the offending user and the list of roles allowed to bypass this check."""
        message = f"User {user.username} is not assigned to any person.\nExempted roles: {exempted_roles}."
        super().__init__(message)


def check_user_person_assignment(user):
    """Check if user is assigned to a person."""
    for role in EXEMPTED_ROLES:
        if has_role(user, role):
            return

    try:
        _ = user.person  # noqa: B018 — attribute access triggers RelatedObjectDoesNotExist
    except mo.User.person.RelatedObjectDoesNotExist as exc:
        raise NoPersonAssignedToUser(user, EXEMPTED_ROLES) from exc
