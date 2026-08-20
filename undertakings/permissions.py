"""This module contains the permission checkers for the undertakings app."""

from typing import Any

from django.contrib.auth.models import User
from rolepermissions.permissions import register_object_checker

from undertakings.models import CostCenter, Undertaking


@register_object_checker()
def access_undertaking(role: Any, user: User, undertaking: Undertaking) -> bool:
    """Check if the user has access to the undertaking."""
    del role
    return type(undertaking).objects.accessible_to(user).filter(pk=undertaking.pk).exists()


@register_object_checker()
def access_cost_center(role: Any, user: User, cost_center: CostCenter) -> bool:
    """Check if the user has access to the cost center."""
    del role
    return type(cost_center).objects.accessible_to(user).filter(pk=cost_center.pk).exists()
