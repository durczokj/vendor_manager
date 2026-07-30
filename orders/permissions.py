"""This file contains the permissions for the people app."""

from rolepermissions.permissions import register_object_checker


@register_object_checker()
def access_order(role, user, order):
    """Check if a user has access to an order."""
    del role
    return type(order).objects.accessible_to(user).filter(pk=order.pk).exists()


@register_object_checker()
def access_order_version(role, user, order_version):
    """Check if a user has access to an order version."""
    del role
    return type(order_version).objects.accessible_to(user).filter(pk=order_version.pk).exists()
