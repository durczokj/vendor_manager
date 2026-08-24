"""P11.T1 tests for /api/v1/dashboards/cost-lines/ and build_cost_lines.

Covers:

* required date_from/date_to (400 on missing)
* span cap (400 when the requested window exceeds
  ``settings.DASHBOARDS_COST_LINES_MAX_DAYS``)
* allow-path: admin can see rows for engagements they can access, every
  denormalized ``*_name`` field is populated where the entity is accessible
* deny-path: a person-role user cannot see another person's engagements
* auth: unauthenticated requests are rejected
"""

from __future__ import annotations

import base64
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.test import override_settings
from rolepermissions.roles import assign_role

from companies.tests.factories import CompanyFactory
from contracts.tests.factories import ContractFactory
from dashboards.services import (
    CostLinesSpanTooLargeError,
    build_cost_lines,
)
from engagements.tests.factories import (
    EngagementFactory,
    EngagementOrderVersionAssignmentFactory,
    EngagementUndertakingAssignmentFactory,
)
from orders.tests.factories import OrderFactory, OrderVersionFactory
from people.tests.factories import PersonFactory
from undertakings.tests.factories import CostCenterFactory, UndertakingFactory

COST_LINES_URL = "/api/v1/dashboards/cost-lines/"


def _auth(username: str, password: str = "testpass") -> dict[str, str]:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"HTTP_AUTHORIZATION": f"Basic {token}"}


@pytest.fixture
def cost_lines_data(db):
    """Minimal dataset with one admin, one person-role user, two engagements."""
    admin_user = User.objects.create_user("cl-adm", None, "testpass")
    person_user = User.objects.create_user("cl-prs", None, "testpass")
    assign_role(admin_user, "admin")
    assign_role(person_user, "person")

    PersonFactory(id="CL0000", first_name="Cl", last_name="Admin", user=admin_user)
    person_a = PersonFactory(id="CL0001", first_name="Alice", last_name="Alpha", user=person_user)
    person_b = PersonFactory(id="CL0002", first_name="Bob", last_name="Beta")

    company = CompanyFactory(id=7101, name="CL Corp", email="cl@example.com")
    contract = ContractFactory(id=7101, name="CL Contract", status="active", size=1)
    order = OrderFactory(id=7101, name="CL Order", company=company)
    order_version = OrderVersionFactory(
        order=order,
        contract=contract,
        version_number=1,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )
    cost_center = CostCenterFactory(id=7101, name="CL CC")
    u_mgr = PersonFactory(id="CL9999", first_name="U", last_name="Mgr")
    undertaking = UndertakingFactory(id=7101, name="CL U", cost_center=cost_center, manager=u_mgr)

    eng_a = EngagementFactory(
        person=person_a,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 2),
        daily_rate=Decimal("100"),
        fte=Decimal("1"),
    )
    EngagementOrderVersionAssignmentFactory(engagement=eng_a, order_version=order_version)
    EngagementUndertakingAssignmentFactory(
        engagement=eng_a,
        undertaking=undertaking,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 2),
        percentage=Decimal("1"),
    )

    eng_b = EngagementFactory(
        person=person_b,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 2),
        daily_rate=Decimal("200"),
        fte=Decimal("1"),
    )
    EngagementOrderVersionAssignmentFactory(engagement=eng_b, order_version=order_version)
    EngagementUndertakingAssignmentFactory(
        engagement=eng_b,
        undertaking=undertaking,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 2),
        percentage=Decimal("1"),
    )

    return {
        "admin_user": admin_user,
        "person_user": person_user,
        "person_a": person_a,
        "person_b": person_b,
        "company": company,
        "order": order,
        "undertaking": undertaking,
        "eng_a": eng_a,
        "eng_b": eng_b,
    }


# ---------------------------------------------------------------------------
# Service layer
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_build_cost_lines_returns_denormalized_names(cost_lines_data):
    """FR-45: every dimension is present per row with a resolved display name."""
    payload = build_cost_lines(
        cost_lines_data["admin_user"],
        (date(2026, 7, 1), date(2026, 7, 2)),
        entity_selection={
            "Person": [],
            "Order": [],
            "Company": [],
            "Undertaking": [],
            "Engagement": [],
        },
    )
    assert payload["date_from"] == "2026-07-01"
    assert payload["date_to"] == "2026-07-02"
    assert payload["count"] == len(payload["rows"])
    assert payload["count"] > 0

    for row in payload["rows"]:
        # Denormalized dimensions
        assert row["person_id"] is not None
        assert row["person_name"] is not None
        assert row["order_name"] is not None
        assert row["company_name"] is not None
        assert row["undertaking_name"] is not None
        # Cost components
        assert "daily_rate" in row
        assert "fte" in row
        assert "is_working_day" in row


@pytest.mark.django_db
def test_build_cost_lines_span_cap(cost_lines_data):
    """A window longer than the configured cap raises CostLinesSpanTooLargeError."""
    with (
        override_settings(DASHBOARDS_COST_LINES_MAX_DAYS=5),
        pytest.raises(CostLinesSpanTooLargeError),
    ):
        build_cost_lines(
            cost_lines_data["admin_user"],
            (date(2026, 7, 1), date(2026, 7, 31)),
            entity_selection={
                "Person": [],
                "Order": [],
                "Company": [],
                "Undertaking": [],
                "Engagement": [],
            },
        )


@pytest.mark.django_db
def test_build_cost_lines_rejects_reversed_dates(cost_lines_data):
    """A ``date_from > date_to`` window raises ``ValueError``."""
    with pytest.raises(ValueError, match="must not be after"):
        build_cost_lines(
            cost_lines_data["admin_user"],
            (date(2026, 7, 2), date(2026, 7, 1)),
            entity_selection={
                "Person": [],
                "Order": [],
                "Company": [],
                "Undertaking": [],
                "Engagement": [],
            },
        )


# ---------------------------------------------------------------------------
# HTTP layer
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_cost_lines_unauthenticated_is_rejected(client, cost_lines_data):
    """FR-22: unauthenticated requests get 401/403."""
    response = client.get(COST_LINES_URL, {"date_from": "2026-07-01", "date_to": "2026-07-02"})
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_cost_lines_missing_dates_returns_400(client, cost_lines_data):
    """``date_from`` and ``date_to`` are required."""
    response = client.get(COST_LINES_URL, **_auth("cl-adm"))
    assert response.status_code == 400
    body = response.json()
    assert "date_from" in body
    assert "date_to" in body


@pytest.mark.django_db
def test_cost_lines_admin_sees_all_engagements(client, cost_lines_data):
    """FR-45: admin role can access every engagement."""
    response = client.get(
        COST_LINES_URL,
        {"date_from": "2026-07-01", "date_to": "2026-07-02"},
        **_auth("cl-adm"),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["date_from"] == "2026-07-01"
    assert body["date_to"] == "2026-07-02"
    person_ids = {row["person_id"] for row in body["rows"]}
    assert cost_lines_data["person_a"].pk in person_ids
    assert cost_lines_data["person_b"].pk in person_ids


@pytest.mark.django_db
def test_cost_lines_person_only_sees_own_engagement(client, cost_lines_data):
    """FR-45: person role only sees rows for engagements they are the person on."""
    response = client.get(
        COST_LINES_URL,
        {"date_from": "2026-07-01", "date_to": "2026-07-02"},
        **_auth("cl-prs"),
    )
    assert response.status_code == 200
    body = response.json()
    person_ids = {row["person_id"] for row in body["rows"]}
    assert person_ids == {cost_lines_data["person_a"].pk}


@pytest.mark.django_db
def test_cost_lines_span_cap_returns_400(client, cost_lines_data):
    """A window wider than the configured cap returns HTTP 400."""
    with override_settings(DASHBOARDS_COST_LINES_MAX_DAYS=5):
        response = client.get(
            COST_LINES_URL,
            {"date_from": "2026-07-01", "date_to": "2026-07-31"},
            **_auth("cl-adm"),
        )
    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.django_db
def test_cost_lines_post_matches_get(client, cost_lines_data):
    """POST and GET must return equivalent payloads for the same filters."""
    payload = {"date_from": "2026-07-01", "date_to": "2026-07-02"}
    r_get = client.get(COST_LINES_URL, payload, **_auth("cl-adm"))
    r_post = client.post(
        COST_LINES_URL,
        payload,
        content_type="application/json",
        **_auth("cl-adm"),
    )
    assert r_get.status_code == 200
    assert r_post.status_code == 200
    assert r_get.json()["count"] == r_post.json()["count"]
