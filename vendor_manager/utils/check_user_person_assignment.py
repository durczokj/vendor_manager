"""Check if user is assigned to a person."""

import django.contrib.auth.models as mo
from rolepermissions.checkers import has_role

EXEMPTED_ROLES = ["admin"]


class NoPersonAssignedToUser(Exception):
    """Exception raised when user is not assigned to a person and is not exempted."""

    def __init__(self, user, exempted_roles):
        """Exception raised when user is not assigned to a person and is not exempted."""
        message = f"User {user.username} is not assigned to any person.\n" f"Exempted roles: {exempted_roles}."
        super().__init__(message)


def check_user_person_assignment(user):
    """Check if user is assigned to a person."""
    for role in EXEMPTED_ROLES:
        if has_role(user, role):
            return

    try:
        user.person
    except mo.User.person.RelatedObjectDoesNotExist:
        raise NoPersonAssignedToUser(user, EXEMPTED_ROLES)
