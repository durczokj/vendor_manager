"""This module contains the permission checkers for the undertakings app."""

from rolepermissions.permissions import register_object_checker

from vendor_manager.roles import Admin, Person, UndertakingManager


@register_object_checker()
def access_undertaking(role, user, undertaking):
    """Check if the user has access to the undertaking."""
    if role == Admin:
        return True

    if role == UndertakingManager:
        managed_undertakings = user.person.managed_undertakings.all()
        if undertaking in managed_undertakings:
            return True

    if role == Person:
        engagements = user.person.engagements.prefetch_related("undertaking_assignments__undertaking")
        undertakings = [a.undertaking for e in engagements for a in e.undertaking_assignments.all()]
        if undertaking in undertakings:
            return True

    return False
