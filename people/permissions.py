"""This file contains the permissions for the people app."""

from rolepermissions.permissions import register_object_checker

from vendor_manager.roles import Admin, Person, UndertakingManager


@register_object_checker()
def access_person(role, user, person):
    """Check if a user has access to a person."""
    if role == Admin:
        return True

    if role == UndertakingManager:
        return True

    if role == Person:
        if person.user == user:
            return True

    return False
