"""This file contains the permissions for the people app."""

from typing import Any

from django.contrib.auth.models import User
from rolepermissions.permissions import register_object_checker

from orders.models import Order, OrderVersion


@register_object_checker()
def access_order(role: Any, user: User, order: Order) -> bool:
    """Check if a user has access to an order."""
    del role
    return type(order).objects.accessible_to(user).filter(pk=order.pk).exists()


@register_object_checker()
def access_order_version(role: Any, user: User, order_version: OrderVersion) -> bool:
    """Check if a user has access to an order version."""
    del role
    return type(order_version).objects.accessible_to(user).filter(pk=order_version.pk).exists()
