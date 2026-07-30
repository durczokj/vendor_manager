"""Define permissions for companies app."""

from rolepermissions.permissions import register_object_checker


@register_object_checker()
def access_company(role, user, company):
    """Check if user has access to company."""
    del role
    return type(company).objects.accessible_to(user).filter(pk=company.pk).exists()
