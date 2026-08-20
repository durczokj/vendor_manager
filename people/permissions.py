"""This file contains the permissions for the people app."""

from typing import Any

from django.contrib.auth.models import User
from rolepermissions.permissions import register_object_checker

from people.models import Person


@register_object_checker()
def access_person(role: Any, user: User, person: Person) -> bool:
    """Check if a user has access to a person."""
    del role
    return type(person).objects.accessible_to(user).filter(pk=person.pk).exists()
