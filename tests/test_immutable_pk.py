"""Regression tests: primary keys must not change on update.

Models with user-chosen primary keys (Person.id as CharField, Company.id
as IntegerField, etc.) previously allowed the pk to be edited via the
update form or PATCHed via the API. Because Django's Model.save() falls
back to INSERT when the UPDATE WHERE clause matches no rows, this created
a duplicate row instead of renaming the original.

The fix disables the pk field in EntityUpdateView.get_form and drops the
pk from validated_data in ImmutablePkSerializerMixin. These tests lock
that behavior in.
"""

from __future__ import annotations

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from rest_framework.test import APIClient
from rolepermissions.roles import assign_role

from companies.models import Company
from companies.tests.factories import CompanyFactory
from people.models import Person
from people.tests.factories import PersonFactory


@pytest.fixture
def admin_client(db) -> Client:
    """Return a Django Client logged in as an admin-role user."""
    user = User.objects.create_user(username="pk-admin", password="x")
    assign_role(user, "admin")
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def admin_api_client(db) -> APIClient:
    """Return a DRF APIClient authenticated as an admin-role user."""
    user = User.objects.create_user(username="pk-admin-api", password="x")
    assign_role(user, "admin")
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_person_update_view_ignores_posted_id(admin_client: Client) -> None:
    """POSTing a different id to person-update must not create a new row."""
    PersonFactory(id="EO1287", first_name="Alice", last_name="Smith")
    before = Person.objects.count()

    response = admin_client.post(
        reverse("person-update", kwargs={"pk": "EO1287"}),
        data={
            "id": "EO9999",  # tampered — must be ignored
            "first_name": "Alice",
            "last_name": "Renamed",
            "description": "",
            "location": "",
            "user": "",
        },
    )

    assert response.status_code in (
        302,
        303,
    ), f"expected redirect, got {response.status_code}: {response.content[:400]!r}"
    assert Person.objects.count() == before, "update must not create a new row"
    assert Person.objects.filter(pk="EO1287").exists(), "original row must still exist"
    assert not Person.objects.filter(pk="EO9999").exists(), "no ghost duplicate row"
    # Other fields still updated normally.
    assert Person.objects.get(pk="EO1287").last_name == "Renamed"


@pytest.mark.django_db
def test_company_update_view_ignores_posted_id(admin_client: Client) -> None:
    """Same guarantee for integer-keyed models: Company.id is immutable."""
    CompanyFactory(id=42, name="Original", email="a@example.com")
    before = Company.objects.count()

    response = admin_client.post(
        reverse("company-update", kwargs={"pk": 42}),
        data={
            "id": 999,  # tampered
            "name": "Renamed",
            "email": "a@example.com",
        },
    )

    assert response.status_code in (302, 303)
    assert Company.objects.count() == before
    assert Company.objects.filter(pk=42).exists()
    assert not Company.objects.filter(pk=999).exists()
    assert Company.objects.get(pk=42).name == "Renamed"


@pytest.mark.django_db
def test_person_api_patch_ignores_id(admin_api_client: APIClient) -> None:
    """PATCH with a different id must not create a new Person row."""
    PersonFactory(id="EO1287", first_name="Alice", last_name="Smith")
    before = Person.objects.count()

    response = admin_api_client.patch(
        "/api/v1/people/EO1287/",
        data={"id": "EO9999", "last_name": "Renamed"},
        format="json",
    )

    assert response.status_code == 200, response.content
    assert Person.objects.count() == before
    assert Person.objects.filter(pk="EO1287").exists()
    assert not Person.objects.filter(pk="EO9999").exists()
    assert Person.objects.get(pk="EO1287").last_name == "Renamed"


@pytest.mark.django_db
def test_person_api_put_ignores_id(admin_api_client: APIClient) -> None:
    """Full PUT with a different id must also preserve the original pk."""
    PersonFactory(id="EO1287", first_name="Alice", last_name="Smith")
    before = Person.objects.count()

    response = admin_api_client.put(
        "/api/v1/people/EO1287/",
        data={
            "id": "EO9999",
            "first_name": "Alice",
            "last_name": "Renamed",
            "description": "",
            "location": "",
            "user": None,
        },
        format="json",
    )

    assert response.status_code == 200, response.content
    assert Person.objects.count() == before
    assert Person.objects.filter(pk="EO1287").exists()
    assert not Person.objects.filter(pk="EO9999").exists()
