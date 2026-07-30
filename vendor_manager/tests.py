"""Smoke tests for the vendor_manager project.

These are intentionally minimal. Real test coverage lives in the per-app
`tests.py` modules and is filled out in Phase 7 (Test hardening) of the
implementation plan.
"""

from django.conf import settings
from django.test import Client
from django.urls import reverse

from vendor_manager.roles import Admin, Person, UndertakingManager


def test_settings_module_loads() -> None:
    """Django can import the settings module without raising."""
    assert settings.INSTALLED_APPS, "INSTALLED_APPS must not be empty."


def test_health_endpoint_returns_200() -> None:
    """The /health/ probe target must respond with 200 for anonymous callers."""
    client = Client()
    response = client.get(reverse("health"))
    assert response.status_code == 200
    assert response.content == b"ok"


def test_roles_have_expected_permission_sets() -> None:
    """Roles expose the expected canonical permission codenames."""
    expected_permissions = {
        "view_person",
        "view_order",
        "view_company",
        "view_undertaking",
        "view_engagement",
        "view_engagement_order_version_assignment",
        "view_engagement_undertaking_assignment",
        "view_leave",
        "view_contract",
        "add_person",
        "change_person",
        "delete_person",
        "add_order",
        "change_order",
        "delete_order",
        "add_company",
        "change_company",
        "delete_company",
        "add_undertaking",
        "change_undertaking",
        "delete_undertaking",
        "add_engagement",
        "change_engagement",
        "delete_engagement",
        "add_engagement_order_version_assignment",
        "change_engagement_order_version_assignment",
        "delete_engagement_order_version_assignment",
        "add_engagement_undertaking_assignment",
        "change_engagement_undertaking_assignment",
        "delete_engagement_undertaking_assignment",
        "add_leave",
        "change_leave",
        "delete_leave",
        "add_contract",
        "change_contract",
        "delete_contract",
    }

    assert set(Person.available_permissions) == expected_permissions
    assert set(UndertakingManager.available_permissions) == expected_permissions
    assert set(Admin.available_permissions) == expected_permissions

    assert Person.available_permissions["view_person"] is True
    assert Person.available_permissions["view_engagement_undertaking_assignment"] is False
    assert Person.available_permissions["change_leave"] is True
    assert Person.available_permissions["delete_contract"] is False

    assert UndertakingManager.available_permissions["view_engagement_undertaking_assignment"] is True
    assert UndertakingManager.available_permissions["change_undertaking"] is True
    assert UndertakingManager.available_permissions["delete_undertaking"] is True
    assert UndertakingManager.available_permissions["add_order"] is False

    assert Admin.available_permissions["view_engagement_undertaking_assignment"] is True
    assert Admin.available_permissions["add_engagement_undertaking_assignment"] is True
    assert Admin.available_permissions["delete_engagement"] is True
    assert Admin.available_permissions["change_contract"] is False
