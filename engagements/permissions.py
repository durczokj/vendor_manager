"""Define permissions for engagements app."""

from rolepermissions.permissions import register_object_checker

from vendor_manager.roles import Admin, Person, UndertakingManager


@register_object_checker()
def access_engagement(role, user, engagement):
    """Check if user has access to the engagement."""
    if role == Admin:
        return True

    if role == UndertakingManager:
        undertaking_engagements = set()
        for un in user.person.managed_undertakings.all():
            for ass in un.engagement_assignments.all():
                undertaking_engagements.add(ass.engagement)
        if engagement in undertaking_engagements:
            return True

    if role == Person:
        if engagement.person == user.person:
            return True

    return False
