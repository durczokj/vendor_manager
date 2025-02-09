"""Define permissions for engagements app."""

from rolepermissions.permissions import register_object_checker

from vendor_manager.roles import Admin, Person, UndertakingManager


@register_object_checker()
def access_engagement(role, user, engagement):
    """Check if user has access to the engagement."""
    if role == Admin:
        return True

    if role == UndertakingManager:
        return True

    if role == Person:
        if engagement.person == user.person:
            return True

    return False
