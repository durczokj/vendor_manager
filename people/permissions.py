"""This file contains the permissions for the people app."""

from rolepermissions.permissions import register_object_checker


@register_object_checker()
def access_person(role, user, person):
    """Check if a user has access to a person."""
    del role
    return type(person).objects.accessible_to(user).filter(pk=person.pk).exists()
