"""P7.T6 branch-coverage tests for dashboards.selectors.get_accessible_cost_rows.

Focus on edge-case branches that the smoke tests in ``test_services.py`` don't
touch: empty accessible-engagement set, no order-version assignments, present
leaves, under-covered undertaking assignments, no undertaking assignments at
all, invalid entity-filter keys, and pandas NA sanitisation in the output.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from rolepermissions.roles import assign_role

from companies.tests.factories import CompanyFactory
from contracts.tests.factories import ContractFactory
from dashboards.selectors import get_accessible_cost_rows
from engagements.tests.factories import (
    EngagementFactory,
    EngagementOrderVersionAssignmentFactory,
    EngagementUndertakingAssignmentFactory,
)
from leaves.tests.factories import LeaveFactory
from orders.tests.factories import OrderFactory, OrderVersionFactory
from people.tests.factories import PersonFactory
from undertakings.tests.factories import CostCenterFactory, UndertakingFactory


@pytest.fixture
def admin_user(db):
    """Admin-role user with a linked Person."""
    user = User.objects.create_user("ds-admin", None, "pw")
    assign_role(user, "admin")
    PersonFactory(id="DS0001", first_name="Admin", last_name="Sel", user=user)
    return user


@pytest.mark.django_db
def test_returns_empty_when_user_has_no_accessible_engagements(db):
    """FR-45: a person-role user with no engagements gets an empty result."""
    user = User.objects.create_user("ds-empty", None, "pw")
    assign_role(user, "person")
    PersonFactory(id="DS0002", first_name="No", last_name="Eng", user=user)

    assert get_accessible_cost_rows(user) == []


@pytest.mark.django_db
def test_engagement_without_order_version_is_inactive(admin_user):
    """FR-19/FR-45: an engagement with no OV assignment yields no active cost."""
    person = PersonFactory(id="DS0010", first_name="No", last_name="Ov")
    EngagementFactory(
        person=person,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 3),
        daily_rate=Decimal("100"),
        fte=Decimal("1"),
    )

    rows = get_accessible_cost_rows(admin_user)
    assert rows, "expected calendar rows for the engagement"
    assert all(row["cost"] == 0.0 for row in rows)
    assert all(row["order_id"] is None for row in rows)
    assert all(row["company_id"] is None for row in rows)


@pytest.mark.django_db
def test_leave_reduces_availability(admin_user):
    """FR-19/FR-45: an active day overlapping a leave sees availability reduced by the leave percentage."""
    company = CompanyFactory(id=6001, name="Dash Co", email="dash@example.com")
    contract = ContractFactory(id=6001, name="Dash Contract", status="active", size=1)
    order = OrderFactory(id=6001, name="Dash Order", company=company)
    order_version = OrderVersionFactory(
        order=order,
        contract=contract,
        version_number=1,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 3),
    )
    cost_center = CostCenterFactory(id=6001, name="Dash CC")
    dash_mgr = PersonFactory(id="DS0021", first_name="Dash", last_name="Mgr")
    undertaking = UndertakingFactory(id=6001, name="Dash U", cost_center=cost_center, manager=dash_mgr)
    person = PersonFactory(id="DS0020", first_name="Leave", last_name="Ful")
    engagement = EngagementFactory(
        person=person,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 3),
        daily_rate=Decimal("100"),
        fte=Decimal("1"),
    )
    EngagementOrderVersionAssignmentFactory(engagement=engagement, order_version=order_version)
    EngagementUndertakingAssignmentFactory(
        engagement=engagement,
        undertaking=undertaking,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 3),
        percentage=Decimal("1.00"),
    )
    LeaveFactory(
        person=person,
        start_date=date(2024, 1, 2),
        end_date=date(2024, 1, 2),
        percentage=Decimal("0.50"),
    )

    rows = get_accessible_cost_rows(admin_user)
    by_date = {row["date"]: row["cost"] for row in rows}
    assert by_date[date(2024, 1, 1)] == pytest.approx(100.0)
    assert by_date[date(2024, 1, 2)] == pytest.approx(50.0)
    assert by_date[date(2024, 1, 3)] == pytest.approx(100.0)


@pytest.mark.django_db
def test_under_covered_undertaking_assignments_emit_unassigned_row(admin_user, caplog):
    """FR-19/FR-45: an active day with UA percentage < 1 emits an ``undertaking_id=None`` row."""
    company = CompanyFactory(id=6002, name="Under Co", email="under@example.com")
    contract = ContractFactory(id=6002, name="Under Contract", status="active", size=1)
    order = OrderFactory(id=6002, name="Under Order", company=company)
    order_version = OrderVersionFactory(
        order=order,
        contract=contract,
        version_number=1,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
    )
    cost_center = CostCenterFactory(id=6002, name="Under CC")
    under_mgr = PersonFactory(id="DS0031", first_name="Under", last_name="Mgr")
    undertaking = UndertakingFactory(id=6002, name="Under U", cost_center=cost_center, manager=under_mgr)
    person = PersonFactory(id="DS0030", first_name="Under", last_name="Cov")
    engagement = EngagementFactory(
        person=person,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
        daily_rate=Decimal("100"),
        fte=Decimal("1"),
    )
    EngagementOrderVersionAssignmentFactory(engagement=engagement, order_version=order_version)
    EngagementUndertakingAssignmentFactory(
        engagement=engagement,
        undertaking=undertaking,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
        percentage=Decimal("0.40"),
    )

    with caplog.at_level("WARNING", logger="dashboards.selectors"):
        rows = get_accessible_cost_rows(admin_user)

    assert any("Under-covered" in rec.message for rec in caplog.records)
    unassigned = [row for row in rows if row["undertaking_id"] is None]
    assert unassigned, "expected at least one unassigned row for the under-covered day"


@pytest.mark.django_db
def test_active_engagement_without_undertaking_assignments(admin_user):
    """FR-45: an engagement with an active OV but no undertaking assignments is fully unassigned."""
    company = CompanyFactory(id=6003, name="NoUa Co", email="noua@example.com")
    contract = ContractFactory(id=6003, name="NoUa Contract", status="active", size=1)
    order = OrderFactory(id=6003, name="NoUa Order", company=company)
    order_version = OrderVersionFactory(
        order=order,
        contract=contract,
        version_number=1,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
    )
    person = PersonFactory(id="DS0040", first_name="No", last_name="Ua")
    engagement = EngagementFactory(
        person=person,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
        daily_rate=Decimal("100"),
        fte=Decimal("1"),
    )
    EngagementOrderVersionAssignmentFactory(engagement=engagement, order_version=order_version)

    rows = get_accessible_cost_rows(admin_user)
    assert rows
    assert all(row["undertaking_id"] is None for row in rows)
    assert all(row["percentage"] == 1.0 for row in rows)


@pytest.mark.django_db
def test_invalid_entity_filter_key_is_ignored(admin_user):
    """FR-45: unknown class names in ``entity_filters`` are silently skipped."""
    person = PersonFactory(id="DS0050", first_name="Filter", last_name="User")
    EngagementFactory(
        person=person,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 1),
        daily_rate=Decimal("100"),
        fte=Decimal("1"),
    )

    rows = get_accessible_cost_rows(admin_user, entity_filters={"NotARealClass": [1, 2, 3]})
    assert rows, "unknown entity-filter keys must not drop legitimate rows"


@pytest.mark.django_db
def test_missing_company_id_serialises_to_none(admin_user):
    """FR-45: rows whose ``company_id`` is missing (no OV) render as ``None``, not NaN."""
    person = PersonFactory(id="DS0060", first_name="Na", last_name="Serialize")
    EngagementFactory(
        person=person,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 1),
        daily_rate=Decimal("100"),
        fte=Decimal("1"),
    )

    rows = get_accessible_cost_rows(admin_user)
    assert rows
    for row in rows:
        assert row["order_id"] is None
        assert row["company_id"] is None
