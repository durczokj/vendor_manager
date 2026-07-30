"""Define permissions for contracts app."""

from rolepermissions.permissions import register_object_checker


@register_object_checker()
def access_contract(role, user, contract):
    """Check if user has access to the contract."""
    del role
    return type(contract).objects.accessible_to(user).filter(pk=contract.pk).exists()
