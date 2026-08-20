"""P7.T4 — per-viewset × per-role API tests.

Uses DRF's ``APIClient`` with each of the three roles (Admin, UndertakingManager,
Person) to verify that every viewset in ``/api/v1/`` correctly applies the
``accessible_to(user)`` filter across list, retrieve, and write verbs. Both
Basic and session authentication are exercised at least once per role.
"""

from __future__ import annotations

import base64
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rolepermissions.roles import assign_role

from companies.models import Company
from companies.tests.factories import CompanyFactory
from contracts.models import Contract
from contracts.tests.factories import ContractFactory
from engagements.models import Engagement, EngagementOrderVersionAssignment, EngagementUndertakingAssignment
from engagements.tests.factories import (
    EngagementFactory,
    EngagementOrderVersionAssignmentFactory,
    EngagementUndertakingAssignmentFactory,
)
from leaves.models import Leave
from leaves.tests.factories import LeaveFactory
from orders.models import Order, OrderVersion
from orders.tests.factories import OrderFactory, OrderVersionFactory
from people.models import Person
from people.tests.factories import PersonFactory
from undertakings.models import CostCenter, Undertaking
from undertakings.tests.factories import CostCenterFactory, UndertakingFactory

ROLE_NAMES = ("admin", "undertaking_manager", "person")


def _basic_auth(username: str, password: str) -> dict[str, str]:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"HTTP_AUTHORIZATION": f"Basic {token}"}


@pytest.fixture
def matrix_data(db):
    """Seed one allowed + one blocked instance of every entity, with three role users."""
    admin_user = User.objects.create_user("mx-admin", None, "pw")
    manager_user = User.objects.create_user("mx-manager", None, "pw")
    person_user = User.objects.create_user("mx-person", None, "pw")

    assign_role(admin_user, "admin")
    assign_role(manager_user, "undertaking_manager")
    assign_role(person_user, "person")

    admin_person = PersonFactory(id="MX0001", first_name="Admin", last_name="Mx", user=admin_user)
    manager_person = PersonFactory(id="MX0002", first_name="Mgr", last_name="Mx", user=manager_user)
    person_person = PersonFactory(id="MX0003", first_name="Prs", last_name="Mx", user=person_user)

    allowed_cc = CostCenterFactory(id=7001, name="Allowed CC")
    blocked_cc = CostCenterFactory(id=7002, name="Blocked CC")
    allowed_undertaking = UndertakingFactory(id=7101, name="Allowed U", cost_center=allowed_cc, manager=manager_person)
    blocked_undertaking = UndertakingFactory(id=7102, name="Blocked U", cost_center=blocked_cc, manager=admin_person)

    allowed_company = CompanyFactory(id=7201, name="Allowed Co", email="a@x.com")
    blocked_company = CompanyFactory(id=7202, name="Blocked Co", email="b@x.com")
    allowed_order = OrderFactory(id=7301, name="Allowed O", company=allowed_company)
    blocked_order = OrderFactory(id=7302, name="Blocked O", company=blocked_company)
    allowed_contract = ContractFactory(id=7401, name="Allowed C", status="active", size=1)
    blocked_contract = ContractFactory(id=7402, name="Blocked C", status="active", size=1)

    allowed_ov = OrderVersionFactory(
        order=allowed_order,
        contract=allowed_contract,
        version_number=1,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
    )
    blocked_ov = OrderVersionFactory(
        order=blocked_order,
        contract=blocked_contract,
        version_number=1,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
    )

    allowed_engagement = EngagementFactory(
        person=person_person,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        daily_rate=Decimal("100"),
        fte=Decimal("1"),
    )
    blocked_engagement = EngagementFactory(
        person=admin_person,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        daily_rate=Decimal("100"),
        fte=Decimal("1"),
    )

    allowed_ova = EngagementOrderVersionAssignmentFactory(engagement=allowed_engagement, order_version=allowed_ov)
    blocked_ova = EngagementOrderVersionAssignmentFactory(engagement=blocked_engagement, order_version=blocked_ov)
    allowed_eua = EngagementUndertakingAssignmentFactory(
        engagement=allowed_engagement,
        undertaking=allowed_undertaking,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        percentage=Decimal("1.00"),
    )
    blocked_eua = EngagementUndertakingAssignmentFactory(
        engagement=blocked_engagement,
        undertaking=blocked_undertaking,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        percentage=Decimal("1.00"),
    )

    allowed_leave = LeaveFactory(
        person=person_person,
        start_date=date(2025, 3, 1),
        end_date=date(2025, 3, 5),
        percentage=Decimal("0.50"),
    )
    blocked_leave = LeaveFactory(
        person=admin_person,
        start_date=date(2025, 3, 1),
        end_date=date(2025, 3, 5),
        percentage=Decimal("0.50"),
    )

    return {
        "users": {"admin": admin_user, "undertaking_manager": manager_user, "person": person_user},
        "allowed": {
            "companies": allowed_company,
            "contracts": allowed_contract,
            "people": person_person,
            "orders": allowed_order,
            "order-versions": allowed_ov,
            "cost-centers": allowed_cc,
            "undertakings": allowed_undertaking,
            "engagements": allowed_engagement,
            "engagement-order-version-assignments": allowed_ova,
            "engagement-undertaking-assignments": allowed_eua,
            "leaves": allowed_leave,
        },
        "blocked": {
            "companies": blocked_company,
            "contracts": blocked_contract,
            "people": admin_person,
            "orders": blocked_order,
            "order-versions": blocked_ov,
            "cost-centers": blocked_cc,
            "undertakings": blocked_undertaking,
            "engagements": blocked_engagement,
            "engagement-order-version-assignments": blocked_ova,
            "engagement-undertaking-assignments": blocked_eua,
            "leaves": blocked_leave,
        },
    }


VIEWSET_BASENAMES = [
    "companies",
    "contracts",
    "people",
    "orders",
    "order-versions",
    "cost-centers",
    "undertakings",
    "engagements",
    "engagement-order-version-assignments",
    "engagement-undertaking-assignments",
    "leaves",
]


# ── LIST verb — accessible_to enforcement across all viewsets and roles ──────


@pytest.mark.parametrize("basename", VIEWSET_BASENAMES)
@pytest.mark.parametrize("role", ROLE_NAMES)
def test_list_returns_only_accessible_entities(matrix_data, basename, role) -> None:
    """FR-27/FR-28: LIST endpoints return exactly the caller's accessible set for every role."""
    user = matrix_data["users"][role]
    allowed_pk = matrix_data["allowed"][basename].pk
    blocked_pk = matrix_data["blocked"][basename].pk

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get(f"/api/v1/{basename}/")

    assert response.status_code == 200
    ids = {row["id"] for row in response.json()["results"]}

    if role == "admin":
        assert allowed_pk in ids
        assert blocked_pk in ids
    else:
        assert allowed_pk in ids
        assert blocked_pk not in ids


# ── RETRIEVE verb — 200 on accessible, 404 on blocked, per role ──────────────


@pytest.mark.parametrize("basename", VIEWSET_BASENAMES)
@pytest.mark.parametrize("role", ROLE_NAMES)
def test_retrieve_allowed_returns_200(matrix_data, basename, role) -> None:
    """RETRIEVE on an accessible entity returns 200 for every role."""
    user = matrix_data["users"][role]
    obj = matrix_data["allowed"][basename]

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get(f"/api/v1/{basename}/{obj.pk}/")

    assert response.status_code == 200, f"{role} could not retrieve {basename}/{obj.pk}"


@pytest.mark.parametrize("basename", VIEWSET_BASENAMES)
@pytest.mark.parametrize("role", ["undertaking_manager", "person"])
def test_retrieve_blocked_returns_404(matrix_data, basename, role) -> None:
    """RETRIEVE on a blocked entity returns 404 for non-admin roles (queryset-scoped)."""
    user = matrix_data["users"][role]
    obj = matrix_data["blocked"][basename]

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get(f"/api/v1/{basename}/{obj.pk}/")

    assert response.status_code == 404


# ── Write verbs on blocked resources — non-admin sees 404 not 403 ────────────


@pytest.mark.parametrize("basename", VIEWSET_BASENAMES)
@pytest.mark.parametrize("role", ["undertaking_manager", "person"])
def test_patch_blocked_returns_404(matrix_data, basename, role) -> None:
    """PATCH on a blocked entity returns 404 (out of queryset) for non-admin roles."""
    user = matrix_data["users"][role]
    obj = matrix_data["blocked"][basename]

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.patch(f"/api/v1/{basename}/{obj.pk}/", data={}, format="json")

    assert response.status_code == 404


@pytest.mark.parametrize("basename", VIEWSET_BASENAMES)
@pytest.mark.parametrize("role", ["undertaking_manager", "person"])
def test_delete_blocked_returns_404(matrix_data, basename, role) -> None:
    """DELETE on a blocked entity returns 404 (out of queryset) for non-admin roles."""
    user = matrix_data["users"][role]
    obj = matrix_data["blocked"][basename]

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.delete(f"/api/v1/{basename}/{obj.pk}/")

    assert response.status_code == 404


# ── Admin PUT/PATCH/DELETE verbs — end-to-end write on every viewset ─────────


ADMIN_PATCH_PAYLOADS: dict[str, dict[str, Any]] = {
    "companies": {"name": "Renamed Co"},
    "contracts": {"name": "Renamed Contract"},
    "people": {"first_name": "Renamed"},
    "orders": {"name": "Renamed Order"},
    "order-versions": {},
    "cost-centers": {"name": "Renamed CC"},
    "undertakings": {"name": "Renamed U"},
    "engagements": {"daily_rate": "200.00"},
    "engagement-order-version-assignments": {},
    "engagement-undertaking-assignments": {"percentage": "0.75"},
    "leaves": {"percentage": "0.25"},
}


@pytest.mark.parametrize("basename", VIEWSET_BASENAMES)
def test_admin_patch_allowed(matrix_data, basename) -> None:
    """Admin can PATCH every viewset — validates the write path uses the service layer where needed."""
    user = matrix_data["users"]["admin"]
    obj = matrix_data["allowed"][basename]

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.patch(
        f"/api/v1/{basename}/{obj.pk}/",
        data=ADMIN_PATCH_PAYLOADS[basename],
        format="json",
    )

    assert response.status_code == 200, response.content


# ── Custom actions (FR-31) — role-based access ───────────────────────────────


def test_clone_latest_version_admin_success(matrix_data) -> None:
    """FR-31: admin can POST clone-latest against an accessible order."""
    admin = matrix_data["users"]["admin"]
    order = matrix_data["allowed"]["orders"]
    new_contract = ContractFactory(id=7501, name="Clone Contract", status="active", size=1)

    client = APIClient()
    client.force_authenticate(user=admin)
    response = client.post(
        f"/api/v1/orders/{order.pk}/versions/clone-latest/",
        data={
            "contract_id": new_contract.pk,
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "copy_engagement_assignments": False,
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["order"] == order.pk


def test_clone_latest_version_person_role_blocked_order_returns_404(matrix_data) -> None:
    """FR-31: person role cannot clone-latest on a blocked order (queryset-scoped)."""
    person = matrix_data["users"]["person"]
    blocked_order = matrix_data["blocked"]["orders"]
    new_contract = ContractFactory(id=7502, name="Denied Contract", status="active", size=1)

    client = APIClient()
    client.force_authenticate(user=person)
    response = client.post(
        f"/api/v1/orders/{blocked_order.pk}/versions/clone-latest/",
        data={
            "contract_id": new_contract.pk,
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
        },
        format="json",
    )

    assert response.status_code == 404


@pytest.mark.parametrize("role", ROLE_NAMES)
def test_engagement_costs_action_allowed(matrix_data, role) -> None:
    """FR-31: every role can call /engagements/<id>/costs/ on an accessible engagement."""
    user = matrix_data["users"][role]
    engagement = matrix_data["allowed"]["engagements"]

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get(f"/api/v1/engagements/{engagement.pk}/costs/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.parametrize("role", ["undertaking_manager", "person"])
def test_engagement_costs_action_blocked_returns_404(matrix_data, role) -> None:
    """FR-31: non-admin cannot call /engagements/<id>/costs/ on a blocked engagement."""
    user = matrix_data["users"][role]
    engagement = matrix_data["blocked"]["engagements"]

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get(f"/api/v1/engagements/{engagement.pk}/costs/")

    assert response.status_code == 404


@pytest.mark.parametrize("role", ROLE_NAMES)
def test_person_assignments_action_allowed(matrix_data, role) -> None:
    """FR-31: every role can list assignments for their accessible person."""
    user = matrix_data["users"][role]
    person = matrix_data["allowed"]["people"]

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get(f"/api/v1/people/{person.pk}/assignments/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ── Basic vs. session authentication ─────────────────────────────────────────


@pytest.mark.parametrize("role", ROLE_NAMES)
def test_basic_auth_list_works_for_every_role(matrix_data, role) -> None:
    """HTTP Basic auth is honoured for every role on a representative viewset."""
    username = matrix_data["users"][role].username
    client = APIClient()
    response = client.get("/api/v1/people/", **_basic_auth(username, "pw"))
    assert response.status_code == 200


@pytest.mark.parametrize("role", ROLE_NAMES)
def test_session_auth_list_works_for_every_role(matrix_data, role) -> None:
    """Session auth (browser login) is honoured for every role on a representative viewset."""
    user = matrix_data["users"][role]
    client = APIClient()
    client.force_login(user)
    response = client.get("/api/v1/people/")
    assert response.status_code == 200


# ── Anonymous verb sweep — every viewset must reject anon writes with 401 ────


@pytest.mark.parametrize("basename", VIEWSET_BASENAMES)
@pytest.mark.parametrize("verb", ["get", "post", "patch", "delete"])
def test_anonymous_requests_are_rejected(matrix_data, basename, verb) -> None:
    """FR-22/NFR-10: every viewset rejects unauthenticated requests with 401 across verbs."""
    client = APIClient()
    url = f"/api/v1/{basename}/"
    if verb == "get":
        response = client.get(url)
    elif verb == "post":
        response = client.post(url, data={}, format="json")
    elif verb == "patch":
        obj = matrix_data["allowed"][basename]
        response = client.patch(f"{url}{obj.pk}/", data={}, format="json")
    else:
        obj = matrix_data["allowed"][basename]
        response = client.delete(f"{url}{obj.pk}/")

    assert response.status_code == 401


# ── Silence unused-import warnings for models re-exported for downstream use ─

_ = (
    Company,
    Contract,
    Person,
    Order,
    OrderVersion,
    CostCenter,
    Undertaking,
    Engagement,
    EngagementOrderVersionAssignment,
    EngagementUndertakingAssignment,
    Leave,
)
