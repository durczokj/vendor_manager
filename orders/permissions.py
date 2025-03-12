"""This file contains the permissions for the people app."""

from rolepermissions.permissions import register_object_checker

from vendor_manager.roles import Admin, UndertakingManager


@register_object_checker()
def access_order(role, user, order):
    """Check if a user has access to an order."""
    if role == Admin:
        return True

    if role == UndertakingManager:
        undertaking_orders = set()
        for un in user.person.managed_undertakings.all():
            for ass in un.engagement_assignments.all():
                undertaking_orders.add(ass.engagement.order)
        if order in undertaking_orders:
            return True

    return False
