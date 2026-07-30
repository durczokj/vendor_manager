"""Smoke tests for the vendor_manager project.

These are intentionally minimal. Real test coverage lives in the per-app
`tests.py` modules and is filled out in Phase 7 (Test hardening) of the
implementation plan.
"""

from django.conf import settings
from django.test import Client
from django.urls import reverse


def test_settings_module_loads() -> None:
    """Django can import the settings module without raising."""
    assert settings.INSTALLED_APPS, "INSTALLED_APPS must not be empty."


def test_health_endpoint_returns_200() -> None:
    """The /health/ probe target must respond with 200 for anonymous callers."""
    client = Client()
    response = client.get(reverse("health"))
    assert response.status_code == 200
    assert response.content == b"ok"
