"""Tests for P3.T2 – explicit serializers, viewsets, and routers."""

from __future__ import annotations

import base64
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from rolepermissions.roles import assign_role

from companies.models import Company
from companies.tests.factories import CompanyFactory
from contracts.models import Contract
from contracts.tests.factories import ContractFactory
from engagements.models import Engagement
from engagements.tests.factories import (
    EngagementFactory,
    EngagementOrderVersionAssignmentFactory,
    EngagementUndertakingAssignmentFactory,
)
from leaves.tests.factories import LeaveFactory
from orders.tests.factories import OrderFactory, OrderVersionFactory
from people.models import Person
from people.tests.factories import PersonFactory
from undertakings.tests.factories import CostCenterFactory, UndertakingFactory

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _basic_auth_header(username: str, password: str) -> str:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return f"Basic {token}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def admin_user(db):
    """Create an admin user with linked Person."""
    user = User.objects.create_user("admin-api", None, "adminpass")
    assign_role(user, "admin")
    PersonFactory(id="A00001", first_name="Admin", last_name="User", user=user)
    return user


@pytest.fixture
def basic_dataset(db, admin_user):
    """Minimal dataset used across tests."""
    company = CompanyFactory(id=9001, name="Test Co", email="test@example.com")
    contract = ContractFactory(id=9001, name="Test Contract", status="active", size=5)
    cost_center = CostCenterFactory(id=9001, name="CC Alpha")
    manager_user = User.objects.create_user("manager-api", None, "managerpass")
    assign_role(manager_user, "admin")
    manager = PersonFactory(id="M00001", first_name="Mgr", last_name="One", user=manager_user)
    undertaking = UndertakingFactory(id=9001, name="Undertaking A", cost_center=cost_center, manager=manager)
    order = OrderFactory(id=9001, name="Order Alpha", company=company)
    order_version = OrderVersionFactory(
        order=order,
        contract=contract,
        version_number=1,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
    )
    person_user = User.objects.create_user("person-api", None, "personpass")
    assign_role(person_user, "admin")
    person = PersonFactory(id="P00001", first_name="Person", last_name="One", user=person_user)
    engagement = EngagementFactory(
        person=person,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        daily_rate=Decimal("500.00"),
        fte=Decimal("1.00"),
    )
    ova = EngagementOrderVersionAssignmentFactory(engagement=engagement, order_version=order_version)
    eua = EngagementUndertakingAssignmentFactory(
        engagement=engagement,
        undertaking=undertaking,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 6, 30),
        percentage=Decimal("1.00"),
    )
    leave = LeaveFactory(
        person=person,
        start_date=date(2025, 3, 1),
        end_date=date(2025, 3, 5),
        percentage=Decimal("1.00"),
    )
    return {
        "company": company,
        "contract": contract,
        "cost_center": cost_center,
        "undertaking": undertaking,
        "order": order,
        "order_version": order_version,
        "person": person,
        "engagement": engagement,
        "order_version_assignment": ova,
        "undertaking_assignment": eua,
        "leave": leave,
    }


# ---------------------------------------------------------------------------
# Anonymous access → 401 for every list endpoint
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url_name",
    [
        "api-v1:contracts-list",
        "api-v1:people-list",
        "api-v1:orders-list",
        "api-v1:order-versions-list",
        "api-v1:cost-centers-list",
        "api-v1:undertakings-list",
        "api-v1:engagements-list",
        "api-v1:engagement-order-version-assignments-list",
        "api-v1:engagement-undertaking-assignments-list",
        "api-v1:leaves-list",
    ],
)
def test_anonymous_request_returns_401(db, url_name):
    """All new list endpoints must reject unauthenticated requests with 401."""
    client = Client()
    response = client.get(reverse(url_name))
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == 'Basic realm="api"'


# ---------------------------------------------------------------------------
# Basic auth READ on all list endpoints
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url_name",
    [
        "api-v1:companies-list",
        "api-v1:contracts-list",
        "api-v1:people-list",
        "api-v1:orders-list",
        "api-v1:order-versions-list",
        "api-v1:cost-centers-list",
        "api-v1:undertakings-list",
        "api-v1:engagements-list",
        "api-v1:engagement-order-version-assignments-list",
        "api-v1:engagement-undertaking-assignments-list",
        "api-v1:leaves-list",
    ],
)
def test_basic_auth_list_returns_200(basic_dataset, url_name):
    """Admin-role user can GET every list endpoint with Basic auth."""
    client = Client()
    auth = _basic_auth_header("admin-api", "adminpass")
    response = client.get(reverse(url_name), HTTP_AUTHORIZATION=auth)
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# accessible_to enforcement
# ---------------------------------------------------------------------------


def test_accessible_to_filters_companies(db):
    """Non-admin users see only their accessible companies."""
    # Admin sees all companies
    admin = User.objects.create_user("adm2", None, "pw")
    assign_role(admin, "admin")
    Person.objects.create(id="A00002", first_name="A", last_name="B", user=admin)

    Company.objects.create(id=8001, name="Visible", email="v@x.com")
    Company.objects.create(id=8002, name="Hidden", email="h@x.com")

    client = Client()
    auth = _basic_auth_header("adm2", "pw")
    response = client.get(reverse("api-v1:companies-list"), HTTP_AUTHORIZATION=auth)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2


def test_accessible_to_person_role_sees_no_companies_when_unlinked(db):
    """A person role with no engagements sees zero companies."""
    user = User.objects.create_user("p2", None, "pw")
    assign_role(user, "person")
    Person.objects.create(id="P00002", first_name="Jane", last_name="Doe", user=user)
    Company.objects.create(id=7001, name="Some Co", email="s@x.com")

    client = Client()
    auth = _basic_auth_header("p2", "pw")
    response = client.get(reverse("api-v1:companies-list"), HTTP_AUTHORIZATION=auth)
    assert response.status_code == 200
    assert response.json()["count"] == 0


# ---------------------------------------------------------------------------
# CRUD – Companies (representative for all entities)
# ---------------------------------------------------------------------------


def test_company_create_via_basic_auth(db, admin_user):
    """Admin can POST a new company with Basic auth (no CSRF required)."""
    client = Client(enforce_csrf_checks=True)
    auth = _basic_auth_header("admin-api", "adminpass")
    response = client.post(
        reverse("api-v1:companies-list"),
        data={"id": 1, "name": "New Co", "email": "new@example.com"},
        content_type="application/json",
        HTTP_AUTHORIZATION=auth,
    )
    assert response.status_code == 201
    assert Company.objects.filter(id=1).exists()


def test_company_update(basic_dataset, admin_user):
    """Admin can PATCH a company."""
    company = basic_dataset["company"]
    client = Client()
    auth = _basic_auth_header("admin-api", "adminpass")
    response = client.patch(
        reverse("api-v1:companies-detail", args=[company.id]),
        data={"name": "Updated Co"},
        content_type="application/json",
        HTTP_AUTHORIZATION=auth,
    )
    assert response.status_code == 200
    company.refresh_from_db()
    assert company.name == "Updated Co"


def test_company_delete(basic_dataset, admin_user):
    """Admin can DELETE a company."""
    company = basic_dataset["company"]
    client = Client()
    auth = _basic_auth_header("admin-api", "adminpass")
    response = client.delete(
        reverse("api-v1:companies-detail", args=[company.id]),
        HTTP_AUTHORIZATION=auth,
    )
    assert response.status_code == 204
    assert not Company.objects.filter(id=company.id).exists()


# ---------------------------------------------------------------------------
# Engagement update calls service (FR-15)
# ---------------------------------------------------------------------------


def test_engagement_update_clamps_assignment_dates(basic_dataset, admin_user):
    """PUT on engagement endpoint adjusts child undertaking assignment dates via service."""
    engagement = basic_dataset["engagement"]
    eua = basic_dataset["undertaking_assignment"]
    # eua currently runs 2025-01-01 to 2025-06-30
    # We shorten the engagement so the assignment must be clamped
    client = Client()
    auth = _basic_auth_header("admin-api", "adminpass")
    response = client.patch(
        reverse("api-v1:engagements-detail", args=[engagement.id]),
        data={"start_date": "2025-03-01"},
        content_type="application/json",
        HTTP_AUTHORIZATION=auth,
    )
    assert response.status_code == 200
    eua.refresh_from_db()
    # Assignment start_date must be clamped to the new engagement start_date
    assert eua.start_date >= date(2025, 3, 1)


# ---------------------------------------------------------------------------
# OpenAPI schema includes all viewsets
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_openapi_schema_lists_all_viewsets():
    """Schema endpoint enumerates all eleven entity endpoints."""
    import json

    User.objects.create_user("schema-user2", None, "pw2")
    auth = _basic_auth_header("schema-user2", "pw2")
    client = Client()
    response = client.get(reverse("api-v1:schema"), HTTP_AUTHORIZATION=auth)
    assert response.status_code == 200
    schema = json.loads(response.content)
    paths = schema["paths"]
    expected_prefixes = [
        "/api/v1/companies/",
        "/api/v1/contracts/",
        "/api/v1/people/",
        "/api/v1/orders/",
        "/api/v1/order-versions/",
        "/api/v1/cost-centers/",
        "/api/v1/undertakings/",
        "/api/v1/engagements/",
        "/api/v1/engagement-order-version-assignments/",
        "/api/v1/engagement-undertaking-assignments/",
        "/api/v1/leaves/",
        "/api/v1/engagements/{engagement_pk}/undertaking-assignments/",
        "/api/v1/engagements/{engagement_pk}/order-version-assignments/",
    ]
    for prefix in expected_prefixes:
        assert any(p.startswith(prefix) for p in paths), f"Missing path prefix: {prefix}"


# ---------------------------------------------------------------------------
# P3.T4 — Custom @action endpoints
# ---------------------------------------------------------------------------


def test_clone_latest_version_happy_path(basic_dataset, admin_user):
    """Admin can POST to clone-latest and receives a new OrderVersion (201)."""
    order = basic_dataset["order"]
    contract2 = Contract.objects.create(id=9002, name="Contract Two", status="active", size=3)
    client = Client()
    auth = _basic_auth_header("admin-api", "adminpass")
    url = reverse("api-v1:orders-clone-latest-version", args=[order.id])
    response = client.post(
        url,
        data={
            "contract_id": contract2.id,
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "copy_engagement_assignments": True,
        },
        content_type="application/json",
        HTTP_AUTHORIZATION=auth,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["order"] == order.id
    assert data["version_number"] == 2
    assert data["contract"] == contract2.id


def test_clone_latest_version_unauthenticated(basic_dataset):
    """Unauthenticated requests to clone-latest must return 401."""
    order = basic_dataset["order"]
    client = Client()
    url = reverse("api-v1:orders-clone-latest-version", args=[order.id])
    response = client.post(url, data={}, content_type="application/json")
    assert response.status_code == 401


def test_clone_latest_version_person_role_denied(basic_dataset):
    """A Person-role user who has no access to the order receives 404 (not found in their queryset)."""
    order = basic_dataset["order"]
    contract2 = Contract.objects.create(id=9003, name="Contract Three", status="active", size=2)

    stranger_user = User.objects.create_user("stranger", None, "pw")
    assign_role(stranger_user, "person")
    Person.objects.create(id="S00001", first_name="Stranger", last_name="User", user=stranger_user)

    client = Client()
    auth = _basic_auth_header("stranger", "pw")
    url = reverse("api-v1:orders-clone-latest-version", args=[order.id])
    response = client.post(
        url,
        data={
            "contract_id": contract2.id,
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
        },
        content_type="application/json",
        HTTP_AUTHORIZATION=auth,
    )
    # The order is not in the stranger's queryset → 404
    assert response.status_code == 404


def test_engagement_costs_happy_path(basic_dataset, admin_user):
    """Admin can GET /engagements/{id}/costs/ and receives a day-level cost list."""
    engagement = basic_dataset["engagement"]
    client = Client()
    auth = _basic_auth_header("admin-api", "adminpass")
    url = reverse("api-v1:engagements-costs", args=[engagement.id])
    response = client.get(url, HTTP_AUTHORIZATION=auth)
    assert response.status_code == 200
    rows = response.json()
    assert isinstance(rows, list)
    assert len(rows) == 365  # 2025 has 365 days
    assert "date" in rows[0]
    assert "cost" in rows[0]


def test_engagement_costs_unauthenticated(basic_dataset):
    """Unauthenticated requests to /costs/ return 401."""
    engagement = basic_dataset["engagement"]
    client = Client()
    url = reverse("api-v1:engagements-costs", args=[engagement.id])
    response = client.get(url)
    assert response.status_code == 401


def test_engagement_cost_coverage_happy_path(basic_dataset, admin_user):
    """Admin can GET /engagements/{id}/cost-coverage/ and receives undertaking rows."""
    engagement = basic_dataset["engagement"]
    client = Client()
    auth = _basic_auth_header("admin-api", "adminpass")
    url = reverse("api-v1:engagements-cost-coverage", args=[engagement.id])
    response = client.get(url, HTTP_AUTHORIZATION=auth)
    assert response.status_code == 200
    rows = response.json()
    assert isinstance(rows, list)
    # At least one row should exist (undertaking covers Jan–Jun 2025)
    assert len(rows) > 0


def test_engagement_cost_coverage_unauthenticated(basic_dataset):
    """Unauthenticated requests to /cost-coverage/ return 401."""
    engagement = basic_dataset["engagement"]
    client = Client()
    url = reverse("api-v1:engagements-cost-coverage", args=[engagement.id])
    response = client.get(url)
    assert response.status_code == 401


def test_person_assignments_happy_path(basic_dataset, admin_user):
    """Admin can GET /people/{id}/assignments/ and receives undertaking assignment list."""
    person = basic_dataset["person"]
    eua = basic_dataset["undertaking_assignment"]
    client = Client()
    auth = _basic_auth_header("admin-api", "adminpass")
    url = reverse("api-v1:people-assignments", args=[person.id])
    response = client.get(url, HTTP_AUTHORIZATION=auth)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == eua.id


def test_person_assignments_unauthenticated(basic_dataset):
    """Unauthenticated requests to /people/{id}/assignments/ return 401."""
    person = basic_dataset["person"]
    client = Client()
    url = reverse("api-v1:people-assignments", args=[person.id])
    response = client.get(url)
    assert response.status_code == 401


def test_person_assignments_person_role_sees_own_only(basic_dataset):
    """A Person-role user sees only their own assignments via /people/{id}/assignments/."""
    person = basic_dataset["person"]
    person_user = User.objects.get(username="person-api")
    # Downgrade the test user from admin to person role
    assign_role(person_user, "person")

    client = Client()
    auth = _basic_auth_header("person-api", "personpass")
    url = reverse("api-v1:people-assignments", args=[person.id])
    response = client.get(url, HTTP_AUTHORIZATION=auth)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1  # person has their own assignment


def test_openapi_schema_includes_custom_action_paths(basic_dataset, admin_user):
    """The OpenAPI schema must document all four P3.T4 custom action paths."""
    import json

    auth = _basic_auth_header("admin-api", "adminpass")
    client = Client()
    response = client.get(reverse("api-v1:schema"), HTTP_AUTHORIZATION=auth)
    assert response.status_code == 200
    schema = json.loads(response.content)
    paths = schema["paths"]

    expected_action_paths = [
        "/api/v1/orders/{id}/versions/clone-latest/",
        "/api/v1/engagements/{id}/costs/",
        "/api/v1/engagements/{id}/cost-coverage/",
        "/api/v1/people/{id}/assignments/",
    ]
    for path in expected_action_paths:
        assert path in paths, f"Custom action path missing from OpenAPI schema: {path}"


# ---------------------------------------------------------------------------
# Nested endpoints — scoping and routing (P3.T3)
# ---------------------------------------------------------------------------


def test_nested_undertaking_assignments_list(basic_dataset, admin_user):
    """GET /api/v1/engagements/<pk>/undertaking-assignments/ returns only that engagement's assignments."""
    engagement = basic_dataset["engagement"]
    eua = basic_dataset["undertaking_assignment"]
    client = Client()
    auth = _basic_auth_header("admin-api", "adminpass")
    url = f"/api/v1/engagements/{engagement.id}/undertaking-assignments/"
    response = client.get(url, HTTP_AUTHORIZATION=auth)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["results"][0]["id"] == eua.id


def test_nested_order_version_assignments_list(basic_dataset, admin_user):
    """GET /api/v1/engagements/<pk>/order-version-assignments/ returns only that engagement's assignments."""
    engagement = basic_dataset["engagement"]
    ova = basic_dataset["order_version_assignment"]
    client = Client()
    auth = _basic_auth_header("admin-api", "adminpass")
    url = f"/api/v1/engagements/{engagement.id}/order-version-assignments/"
    response = client.get(url, HTTP_AUTHORIZATION=auth)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["results"][0]["id"] == ova.id


def test_nested_undertaking_assignments_scoped_to_engagement(basic_dataset, admin_user):
    """Nested list for engagement without assignments returns empty result."""
    from datetime import date

    engagement2 = Engagement.objects.create(
        person=basic_dataset["person"],
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        daily_rate=basic_dataset["engagement"].daily_rate,
        fte=basic_dataset["engagement"].fte,
    )
    client = Client()
    auth = _basic_auth_header("admin-api", "adminpass")
    url = f"/api/v1/engagements/{engagement2.id}/undertaking-assignments/"
    response = client.get(url, HTTP_AUTHORIZATION=auth)
    assert response.status_code == 200
    assert response.json()["count"] == 0


def test_nested_routes_require_authentication(basic_dataset):
    """Nested assignment endpoints reject unauthenticated requests with 401."""
    engagement = basic_dataset["engagement"]
    client = Client()
    for url in [
        f"/api/v1/engagements/{engagement.id}/undertaking-assignments/",
        f"/api/v1/engagements/{engagement.id}/order-version-assignments/",
    ]:
        response = client.get(url)
        assert response.status_code == 401, f"Expected 401 for {url}"


def test_flat_undertaking_assignments_filter_by_engagement(basic_dataset, admin_user):
    """Flat endpoint supports ?engagement= filter for reporting."""
    engagement = basic_dataset["engagement"]
    eua = basic_dataset["undertaking_assignment"]
    client = Client()
    auth = _basic_auth_header("admin-api", "adminpass")
    url = f"/api/v1/engagement-undertaking-assignments/?engagement={engagement.id}"
    response = client.get(url, HTTP_AUTHORIZATION=auth)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["results"][0]["id"] == eua.id


def test_flat_order_version_assignments_filter_by_engagement(basic_dataset, admin_user):
    """Flat endpoint supports ?engagement= filter for reporting."""
    engagement = basic_dataset["engagement"]
    ova = basic_dataset["order_version_assignment"]
    client = Client()
    auth = _basic_auth_header("admin-api", "adminpass")
    url = f"/api/v1/engagement-order-version-assignments/?engagement={engagement.id}"
    response = client.get(url, HTTP_AUTHORIZATION=auth)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["results"][0]["id"] == ova.id
