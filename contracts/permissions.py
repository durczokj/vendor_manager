"""Define permissions for contracts app."""

from typing import Any

from django.contrib.auth.models import User
from rolepermissions.permissions import register_object_checker

from contracts.models import Contract


@register_object_checker()
def access_contract(role: Any, user: User, contract: Contract) -> bool:
    """Check if user has access to the contract."""
    del role
    return type(contract).objects.accessible_to(user).filter(pk=contract.pk).exists()
