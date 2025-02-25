"""Define permissions for companies app."""

from rolepermissions.permissions import register_object_checker

from vendor_manager.roles import Admin, Person, UndertakingManager


@register_object_checker()
def access_company(role, user, company):
    """Check if user has access to company."""
    if role == Admin:
        return True

    if role == UndertakingManager:
        undertaking_companies = set()
        for un in user.person.managed_undertakings.all():
            for ass in un.engagement_assignments.all():
                undertaking_companies.add(ass.engagement.order.company)
        if company in undertaking_companies:
            return True

    if role == Person:
        companies = [e.order.company for e in user.person.engagements.all()]
        if company in companies:
            return True

    return False
