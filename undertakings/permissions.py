"""This module contains the permission checkers for the undertakings app."""

from rolepermissions.permissions import register_object_checker


@register_object_checker()
def access_undertaking(role, user, undertaking):
    """Check if the user has access to the undertaking."""
    del role
    return type(undertaking).objects.accessible_to(user).filter(pk=undertaking.pk).exists()


@register_object_checker()
def access_cost_center(role, user, cost_center):
    """Check if the user has access to the cost center."""
    del role
    return type(cost_center).objects.accessible_to(user).filter(pk=cost_center.pk).exists()
