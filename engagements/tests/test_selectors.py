from datetime import date

import pytest
from pandas import Timestamp

from companies.tests.factories import CompanyFactory
from contracts.tests.factories import ContractFactory
from engagements.models import EngagementUndertakingAssignment
from engagements.selectors import CoverageOverAllocationError, engagement_cost_coverage, engagement_costs
from engagements.tests.factories import (
    EngagementFactory,
    EngagementOrderVersionAssignmentFactory,
    EngagementUndertakingAssignmentFactory,
)
from leaves.tests.factories import LeaveFactory
from orders.tests.factories import OrderFactory, OrderVersionFactory
from people.tests.factories import PersonFactory, UserFactory
from undertakings.tests.factories import CostCenterFactory, UndertakingFactory


@pytest.fixture
def engagement_fixture():
    company = CompanyFactory(id=1, name="Company 1", email="company1@example.com")
    contract = ContractFactory(id=1, name="Contract 1", status="active", size=1)
    order = OrderFactory(id=1, name="Order 1", company=company)
    order_version = OrderVersionFactory(
        order=order,
        contract=contract,
        version_number=1,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
    )
    user = UserFactory(username="user-1")
    person = PersonFactory(id="000001", first_name="Jane", last_name="Doe", user=user)
    engagement = EngagementFactory(
        person=person,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 3),
        daily_rate=100,
        fte=0.5,
    )
    EngagementOrderVersionAssignmentFactory(engagement=engagement, order_version=order_version)
    LeaveFactory(person=person, start_date=date(2024, 1, 2), end_date=date(2024, 1, 2), percentage=0.2)

    cost_center = CostCenterFactory(id=1, name="CC-1")
    undertaking_a = UndertakingFactory(id=1, name="A", cost_center=cost_center, manager=person)
    undertaking_b = UndertakingFactory(id=2, name="B", cost_center=cost_center, manager=person)
    EngagementUndertakingAssignmentFactory(
        engagement=engagement,
        undertaking=undertaking_a,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
        percentage=0.6,
    )
    EngagementUndertakingAssignmentFactory(
        engagement=engagement,
        undertaking=undertaking_b,
        start_date=date(2024, 1, 2),
        end_date=date(2024, 1, 2),
        percentage=0.2,
    )
    return engagement, undertaking_a, undertaking_b


@pytest.mark.django_db
def test_engagement_costs_returns_expected_daily_values(engagement_fixture):
    engagement, _, _ = engagement_fixture

    assert engagement_costs(engagement) == [
        {"date": Timestamp("2024-01-01"), "cost": 50.0},
        {"date": Timestamp("2024-01-02"), "cost": 40.0},
        {"date": Timestamp("2024-01-03"), "cost": 0.0},
    ]


@pytest.mark.django_db
def test_engagement_cost_coverage_returns_expected_rows(engagement_fixture):
    engagement, undertaking_a, undertaking_b = engagement_fixture

    rows = engagement_cost_coverage(engagement)
    normalized = [(row["date"], row["undertaking"], round(row["percentage"], 8)) for row in rows]
    assert normalized == [
        (Timestamp("2024-01-01"), undertaking_a, 0.6),
        (Timestamp("2024-01-02"), undertaking_a, 0.6),
        (Timestamp("2024-01-02"), undertaking_b, 0.2),
        (Timestamp("2024-01-01"), None, 0.4),
        (Timestamp("2024-01-02"), None, 0.2),
    ]


@pytest.mark.django_db
def test_engagement_cost_coverage_raises_over_allocation_error(engagement_fixture):
    engagement, undertaking_a, _ = engagement_fixture
    cost_center = undertaking_a.cost_center
    person = engagement.person
    undertaking_c = UndertakingFactory(id=3, name="C", cost_center=cost_center, manager=person)
    EngagementUndertakingAssignment(
        engagement=engagement,
        undertaking=undertaking_c,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 1),
        percentage=0.5,
    ).save()

    with pytest.raises(CoverageOverAllocationError):
        engagement_cost_coverage(engagement)


# ── Empty-graph edge cases (branch coverage for FR-19 selectors) ──────────────


@pytest.mark.django_db
def test_engagement_costs_zero_when_no_order_version_assignments():
    """FR-19: with no order-version assignments the daily cost is zero across the span."""
    person = PersonFactory(id="000010", first_name="No", last_name="OV")
    engagement = EngagementFactory(
        person=person,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
        daily_rate=100,
        fte=1,
    )

    rows = engagement_costs(engagement)
    assert [row["cost"] for row in rows] == [0.0, 0.0]


@pytest.mark.django_db
def test_engagement_costs_full_availability_when_person_has_no_leaves():
    """FR-19: with no leave rows availability is 1.0 for every active day."""
    company = CompanyFactory(id=100, name="Company 100", email="co100@example.com")
    contract = ContractFactory(id=100, name="Contract 100", status="active", size=1)
    order = OrderFactory(id=100, name="Order 100", company=company)
    order_version = OrderVersionFactory(
        order=order,
        contract=contract,
        version_number=1,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
    )
    person = PersonFactory(id="000011", first_name="Leave", last_name="Less")
    engagement = EngagementFactory(
        person=person,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
        daily_rate=100,
        fte=1,
    )
    EngagementOrderVersionAssignmentFactory(engagement=engagement, order_version=order_version)

    rows = engagement_costs(engagement)
    assert [row["cost"] for row in rows] == [100.0, 100.0]


@pytest.mark.django_db
def test_engagement_cost_coverage_empty_when_no_assignments_at_all():
    """FR-19: with neither undertaking nor order-version assignments the payload is empty."""
    person = PersonFactory(id="000013", first_name="None", last_name="AtAll")
    engagement = EngagementFactory(
        person=person,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
        daily_rate=100,
        fte=1,
    )

    assert engagement_cost_coverage(engagement) == []
