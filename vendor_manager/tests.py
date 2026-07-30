"""Smoke tests for the vendor_manager project.

These are intentionally minimal. Real test coverage lives in the per-app
`tests.py` modules and is filled out in Phase 7 (Test hardening) of the
implementation plan.
"""

import base64
import json

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import Client
from django.urls import reverse

from companies.models import Company
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


@pytest.mark.django_db
def test_api_schema_requires_auth_and_returns_openapi() -> None:
    """Schema endpoint authenticates with HTTP Basic and returns OpenAPI JSON."""
    user = User.objects.create_user("staff-user", None, "strong-password", is_staff=True)
    auth = base64.b64encode(f"{user.username}:strong-password".encode()).decode()

    client = Client()
    response = client.get(reverse("api-v1:schema"), HTTP_AUTHORIZATION=f"Basic {auth}")

    assert response.status_code == 200
    assert json.loads(response.content)["openapi"].startswith("3.")


@pytest.mark.django_db
def test_api_companies_anonymous_request_is_401_with_basic_challenge() -> None:
    """Anonymous clients are challenged with HTTP Basic for API endpoints."""
    client = Client()
    response = client.get(reverse("api-v1:companies-list"))

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == 'Basic realm="api"'


@pytest.mark.django_db
def test_api_companies_session_post_without_csrf_is_403() -> None:
    """Session-authenticated writes enforce CSRF protection."""
    user = User.objects.create_user("session-user", None, "strong-password", is_staff=True)
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)

    response = client.post(
        reverse("api-v1:companies-list"),
        data=json.dumps({"id": 2001, "name": "Session Co", "email": "session@example.com"}),
        content_type="application/json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_api_companies_basic_post_without_csrf_is_201() -> None:
    """HTTP Basic-authenticated writes are CSRF-exempt and can create records."""
    user = User.objects.create_user("basic-user", None, "strong-password", is_staff=True)
    auth = base64.b64encode(f"{user.username}:strong-password".encode()).decode()
    client = Client(enforce_csrf_checks=True)

    response = client.post(
        reverse("api-v1:companies-list"),
        data=json.dumps({"id": 2002, "name": "Basic Co", "email": "basic@example.com"}),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Basic {auth}",
    )

    assert response.status_code == 201


@pytest.mark.django_db
def test_api_companies_model_validation_error_returns_drf_400_shape(monkeypatch) -> None:
    """Django model ValidationError maps to DRF's 400 error response shape."""
    user = User.objects.create_user("invalid-company-user", None, "strong-password", is_staff=True)
    auth = base64.b64encode(f"{user.username}:strong-password".encode()).decode()
    client = Client()
    original_save = Company.save

    def fail_save(self, *args, **kwargs):
        if self.pk == 2003:
            raise DjangoValidationError("bad company data")
        return original_save(self, *args, **kwargs)

    monkeypatch.setattr(Company, "save", fail_save)

    response = client.post(
        reverse("api-v1:companies-list"),
        data=json.dumps({"id": 2003, "name": "Invalid Co", "email": "invalid@example.com"}),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Basic {auth}",
    )

    assert response.status_code == 400
    assert response.json() == {"non_field_errors": ["bad company data"]}
