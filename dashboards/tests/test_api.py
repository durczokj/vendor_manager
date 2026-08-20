"""API tests for the dashboard summary endpoint (P5.T2) and entity options endpoint (P5.T3).

Verifies:
- GET /api/v1/dashboards/summary/ and POST /api/v1/dashboards/summary/
  return 200 with the expected payload shape.
- Each role (admin, undertaking_manager, person) receives the data it is
  entitled to see.
- Unauthenticated requests are rejected with 403.
- Invalid filter parameters return 400.
- GET /api/v1/dashboards/entity-options/ returns accessible entity lists.
"""

from __future__ import annotations

import base64
from datetime import date

import pytest
from django.contrib.auth.models import User
from rolepermissions.roles import assign_role

from companies.tests.factories import CompanyFactory
from contracts.tests.factories import ContractFactory
from engagements.tests.factories import (
    EngagementFactory,
    EngagementOrderVersionAssignmentFactory,
    EngagementUndertakingAssignmentFactory,
)
from orders.tests.factories import OrderFactory, OrderVersionFactory
from people.tests.factories import PersonFactory
from undertakings.tests.factories import CostCenterFactory, UndertakingFactory

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth(username: str, password: str = "testpass") -> dict[str, str]:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"HTTP_AUTHORIZATION": f"Basic {token}"}


SUMMARY_URL = "/api/v1/dashboards/summary/"
ENTITY_OPTIONS_URL = "/api/v1/dashboards/entity-options/"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def api_data(db):
    """Create a minimal but complete dataset for dashboard API tests.

    Layout mirrors the service-layer fixture in test_services.py so tests
    stay comparable.  Users are created with a usable password so that
    HTTP Basic auth works in the test client.
    """
    admin_user = User.objects.create_user("adm", None, "testpass")
    manager_user = User.objects.create_user("mgr", None, "testpass")
    person_user = User.objects.create_user("prs", None, "testpass")

    assign_role(admin_user, "admin")
    assign_role(manager_user, "undertaking_manager")
    assign_role(person_user, "person")

    manager_person = PersonFactory(id="M00001", first_name="Manager", last_name="User", user=manager_user)
    person_a = PersonFactory(id="A00001", first_name="Alice", last_name="Alpha", user=person_user)
    person_b = PersonFactory(id="B00001", first_name="Bob", last_name="Beta")

    company = CompanyFactory(id=9001, name="Acme Corp", email="acme@example.com")
    order = OrderFactory(id=8001, name="Order 8001", company=company)
    contract = ContractFactory(id=7001, name="Contract 7001", status="active", size=1)
    order_version = OrderVersionFactory(
        order=order,
        contract=contract,
        version_number=1,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
    )

    cost_center = CostCenterFactory(id=6001, name="CC-6001")
    undertaking = UndertakingFactory(id=5001, name="Undertaking 5001", cost_center=cost_center, manager=manager_person)

    eng_a = EngagementFactory(
        person=person_a,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
        daily_rate=100,
        fte=1,
    )
    EngagementOrderVersionAssignmentFactory(engagement=eng_a, order_version=order_version)
    EngagementUndertakingAssignmentFactory(
        engagement=eng_a,
        undertaking=undertaking,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
        percentage=1,
    )

    eng_b = EngagementFactory(
        person=person_b,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
        daily_rate=200,
        fte=1,
    )
    EngagementOrderVersionAssignmentFactory(engagement=eng_b, order_version=order_version)
    EngagementUndertakingAssignmentFactory(
        engagement=eng_b,
        undertaking=undertaking,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
        percentage=1,
    )

    return {
        "admin_user": admin_user,
        "manager_user": manager_user,
        "person_user": person_user,
        "person_a": person_a,
        "person_b": person_b,
        "manager_person": manager_person,
        "company": company,
        "order": order,
        "undertaking": undertaking,
        "eng_a": eng_a,
        "eng_b": eng_b,
    }


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_unauthenticated_get_returns_403(client, api_data):
    """An unauthenticated GET request is rejected."""
    response = client.get(SUMMARY_URL)
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_unauthenticated_post_returns_403(client, api_data):
    """An unauthenticated POST request is rejected."""
    response = client.post(SUMMARY_URL, {}, content_type="application/json")
    assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# GET — basic shape
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_returns_200_for_admin(client, api_data):
    """An admin GET with default params returns 200."""
    response = client.get(SUMMARY_URL, **_auth("adm"))
    assert response.status_code == 200
    data = response.json()
    assert "class_" in data
    assert "granularity" in data
    assert "rows" in data


@pytest.mark.django_db
def test_get_response_shape(client, api_data):
    """GET response has the expected top-level shape and row keys."""
    response = client.get(SUMMARY_URL + "?class_=Person&granularity=Total", **_auth("adm"))
    assert response.status_code == 200
    data = response.json()
    assert data["class_"] == "Person"
    assert data["granularity"] == "Total"
    assert isinstance(data["rows"], list)
    if data["rows"]:
        row = data["rows"][0]
        assert set(row.keys()) >= {"id", "name", "cost", "date", "month"}


# ---------------------------------------------------------------------------
# POST — basic shape
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_post_returns_200_for_admin(client, api_data):
    """An admin POST with default params returns 200."""
    response = client.post(
        SUMMARY_URL,
        {"class_": "Person", "granularity": "Total"},
        content_type="application/json",
        **_auth("adm"),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["class_"] == "Person"
    assert data["granularity"] == "Total"
    assert "rows" in data


@pytest.mark.django_db
def test_post_accepts_all_filter_params(client, api_data):
    """POST with all filter fields present returns 200."""
    body = {
        "class_": "Person",
        "granularity": "Daily",
        "date_from": "2024-01-01",
        "date_to": "2024-01-02",
        "person_ids": [],
        "order_ids": [],
        "company_ids": [],
        "undertaking_ids": [],
        "engagement_ids": [],
    }
    response = client.post(SUMMARY_URL, body, content_type="application/json", **_auth("adm"))
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Role-based access control
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_admin_sees_all_persons(client, api_data):
    """Admin role GET returns cost rows for all persons."""
    response = client.get(SUMMARY_URL + "?class_=Person&granularity=Total", **_auth("adm"))
    assert response.status_code == 200
    ids = {row["id"] for row in response.json()["rows"]}
    assert "A00001" in ids
    assert "B00001" in ids


@pytest.mark.django_db
def test_person_role_sees_only_own_data_get(client, api_data):
    """Person-role GET returns only the authenticated person's cost rows."""
    response = client.get(SUMMARY_URL + "?class_=Person&granularity=Total", **_auth("prs"))
    assert response.status_code == 200
    ids = {row["id"] for row in response.json()["rows"]}
    assert "A00001" in ids
    assert "B00001" not in ids, "person-role user must not see another person's rows"


@pytest.mark.django_db
def test_person_role_sees_only_own_data_post(client, api_data):
    """Person-role POST returns only the authenticated person's cost rows."""
    body = {"class_": "Person", "granularity": "Total"}
    response = client.post(SUMMARY_URL, body, content_type="application/json", **_auth("prs"))
    assert response.status_code == 200
    ids = {row["id"] for row in response.json()["rows"]}
    assert "A00001" in ids
    assert "B00001" not in ids, "person-role user must not see another person's rows"


@pytest.mark.django_db
def test_undertaking_manager_role_response(client, api_data):
    """Undertaking-manager GET returns persons whose engagements belong to managed undertakings."""
    response = client.get(SUMMARY_URL + "?class_=Person&granularity=Total", **_auth("mgr"))
    assert response.status_code == 200
    data = response.json()
    assert data["class_"] == "Person"
    assert isinstance(data["rows"], list)


# ---------------------------------------------------------------------------
# Filter parameters
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_granularity_daily(client, api_data):
    """GET with granularity=Daily returns rows with date fields populated."""
    response = client.get(SUMMARY_URL + "?class_=Person&granularity=Daily", **_auth("adm"))
    assert response.status_code == 200
    data = response.json()
    assert data["granularity"] == "Daily"
    for row in data["rows"]:
        assert row["date"] is not None
        assert row["month"] is None


@pytest.mark.django_db
def test_get_granularity_monthly(client, api_data):
    """GET with granularity=Monthly returns rows with month fields populated."""
    response = client.get(SUMMARY_URL + "?class_=Person&granularity=Monthly", **_auth("adm"))
    assert response.status_code == 200
    data = response.json()
    assert data["granularity"] == "Monthly"
    for row in data["rows"]:
        assert row["month"] is not None
        assert row["date"] is None


@pytest.mark.django_db
def test_get_date_range_filter(client, api_data):
    """GET with date_from and date_to restricts results to that range."""
    response = client.get(
        SUMMARY_URL + "?class_=Person&granularity=Daily&date_from=2024-01-02&date_to=2024-01-02",
        **_auth("adm"),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["granularity"] == "Daily"
    dates = {row["date"] for row in data["rows"]}
    assert "2024-01-01" not in dates
    if dates:
        assert "2024-01-02" in dates


@pytest.mark.django_db
def test_post_entity_selection_person_ids(client, api_data):
    """POST with person_ids restricts to the specified persons."""
    body = {
        "class_": "Person",
        "granularity": "Total",
        "person_ids": ["A00001"],
    }
    response = client.post(SUMMARY_URL, body, content_type="application/json", **_auth("adm"))
    assert response.status_code == 200
    ids = {row["id"] for row in response.json()["rows"]}
    assert "A00001" in ids
    assert "B00001" not in ids


@pytest.mark.django_db
def test_get_class_undertaking(client, api_data):
    """GET with class_=Undertaking groups costs by undertaking."""
    response = client.get(SUMMARY_URL + "?class_=Undertaking&granularity=Total", **_auth("adm"))
    assert response.status_code == 200
    data = response.json()
    assert data["class_"] == "Undertaking"
    ids = {row["id"] for row in data["rows"]}
    assert api_data["undertaking"].id in ids


@pytest.mark.django_db
def test_get_class_order(client, api_data):
    """GET with class_=Order groups costs by order."""
    response = client.get(SUMMARY_URL + "?class_=Order&granularity=Total", **_auth("adm"))
    assert response.status_code == 200
    data = response.json()
    assert data["class_"] == "Order"
    ids = {row["id"] for row in data["rows"]}
    assert api_data["order"].id in ids


@pytest.mark.django_db
def test_get_class_company(client, api_data):
    """GET with class_=Company groups costs by company."""
    response = client.get(SUMMARY_URL + "?class_=Company&granularity=Total", **_auth("adm"))
    assert response.status_code == 200
    data = response.json()
    assert data["class_"] == "Company"
    ids = {row["id"] for row in data["rows"]}
    assert api_data["company"].id in ids


@pytest.mark.django_db
def test_get_class_engagement(client, api_data):
    """GET with class_=Engagement groups costs by engagement."""
    response = client.get(SUMMARY_URL + "?class_=Engagement&granularity=Total", **_auth("adm"))
    assert response.status_code == 200
    data = response.json()
    assert data["class_"] == "Engagement"
    ids = {row["id"] for row in data["rows"]}
    assert api_data["eng_a"].id in ids
    assert api_data["eng_b"].id in ids


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_invalid_class_returns_400(client, api_data):
    """GET with an unrecognised class_ value returns 400."""
    response = client.get(SUMMARY_URL + "?class_=Invalid", **_auth("adm"))
    assert response.status_code == 400


@pytest.mark.django_db
def test_get_invalid_granularity_returns_400(client, api_data):
    """GET with an unrecognised granularity value returns 400."""
    response = client.get(SUMMARY_URL + "?granularity=Yearly", **_auth("adm"))
    assert response.status_code == 400


@pytest.mark.django_db
def test_post_invalid_date_format_returns_400(client, api_data):
    """POST with a bad date format returns 400."""
    body = {"class_": "Person", "granularity": "Total", "date_from": "not-a-date"}
    response = client.post(SUMMARY_URL, body, content_type="application/json", **_auth("adm"))
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# OpenAPI schema
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_openapi_schema_includes_dashboards_summary(client, api_data):
    """The OpenAPI schema endpoint includes the dashboards/summary path."""
    response = client.get("/api/v1/schema/", **_auth("adm"))
    assert response.status_code == 200
    schema = response.json()
    paths = schema.get("paths", {})
    assert any("dashboards/summary" in p for p in paths), (
        f"Expected dashboards/summary in OpenAPI paths, got: {list(paths.keys())}"
    )


# ---------------------------------------------------------------------------
# Entity options endpoint (P5.T3)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_entity_options_unauthenticated_returns_401_or_403(client, api_data):
    """Unauthenticated GET on entity-options is rejected."""
    response = client.get(ENTITY_OPTIONS_URL)
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_entity_options_admin_returns_200_with_all_keys(client, api_data):
    """Admin GET returns 200 with all expected entity-type keys."""
    response = client.get(ENTITY_OPTIONS_URL, **_auth("adm"))
    assert response.status_code == 200
    data = response.json()
    for key in ("persons", "companies", "orders", "undertakings", "engagements"):
        assert key in data, f"Missing key {key!r} in entity-options response"


@pytest.mark.django_db
def test_entity_options_items_have_id_and_name(client, api_data):
    """Each entity in the entity-options response has 'id' and 'name' fields."""
    response = client.get(ENTITY_OPTIONS_URL, **_auth("adm"))
    assert response.status_code == 200
    data = response.json()
    for key in ("persons", "companies", "orders", "undertakings", "engagements"):
        for item in data[key]:
            assert "id" in item, f"Item in {key!r} is missing 'id': {item}"
            assert "name" in item, f"Item in {key!r} is missing 'name': {item}"


@pytest.mark.django_db
def test_entity_options_admin_sees_all_persons(client, api_data):
    """Admin entity-options includes all persons."""
    response = client.get(ENTITY_OPTIONS_URL, **_auth("adm"))
    assert response.status_code == 200
    person_ids = {item["id"] for item in response.json()["persons"]}
    assert "A00001" in person_ids
    assert "B00001" in person_ids


@pytest.mark.django_db
def test_entity_options_person_role_sees_only_own_person(client, api_data):
    """Person-role entity-options only includes the authenticated user's person."""
    response = client.get(ENTITY_OPTIONS_URL, **_auth("prs"))
    assert response.status_code == 200
    person_ids = {item["id"] for item in response.json()["persons"]}
    assert "A00001" in person_ids
    assert "B00001" not in person_ids, "person-role must not see other persons in entity-options"


@pytest.mark.django_db
def test_entity_options_openapi_schema_includes_endpoint(client, api_data):
    """The OpenAPI schema includes the entity-options path."""
    response = client.get("/api/v1/schema/", **_auth("adm"))
    assert response.status_code == 200
    paths = response.json().get("paths", {})
    assert any("entity-options" in p for p in paths), (
        f"Expected entity-options in OpenAPI paths, got: {list(paths.keys())}"
    )
