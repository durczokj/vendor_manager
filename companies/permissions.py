"""Define permissions for companies app."""

from typing import Any

from django.contrib.auth.models import User
from rolepermissions.permissions import register_object_checker

from companies.models import Company


@register_object_checker()
def access_company(role: Any, user: User, company: Company) -> bool:
    """Check if user has access to company."""
    del role
    return type(company).objects.accessible_to(user).filter(pk=company.pk).exists()
