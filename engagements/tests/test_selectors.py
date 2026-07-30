from datetime import date

import pytest
from django.contrib.auth.models import User
from pandas import Timestamp

from companies.models import Company
from contracts.models import Contract
from engagements.models import Engagement, EngagementOrderVersionAssignment, EngagementUndertakingAssignment
from engagements.selectors import CoverageOverAllocationError, engagement_cost_coverage, engagement_costs
from leaves.models import Leave
from orders.models import Order, OrderVersion
from people.models import Person
from undertakings.models import CostCenter, Undertaking


@pytest.fixture
def engagement_fixture():
    company = Company.objects.create(id=1, name="Company 1", email="company1@example.com")
    contract = Contract.objects.create(id=1, name="Contract 1", status="active", size=1)
    order = Order.objects.create(id=1, name="Order 1", company=company)
    order_version = OrderVersion.objects.create(
        order=order,
        contract=contract,
        version_number=1,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
    )
    user = User.objects.create(username="user-1")
    person = Person.objects.create(id="000001", first_name="Jane", last_name="Doe", user=user)
    engagement = Engagement.objects.create(
        person=person,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 3),
        daily_rate=100,
        fte=0.5,
    )
    EngagementOrderVersionAssignment(engagement=engagement, order_version=order_version).save()
    Leave.objects.create(person=person, start_date=date(2024, 1, 2), end_date=date(2024, 1, 2), percentage=0.2)

    cost_center = CostCenter.objects.create(id=1, name="CC-1")
    undertaking_a = Undertaking.objects.create(id=1, name="A", cost_center=cost_center, manager=person)
    undertaking_b = Undertaking.objects.create(id=2, name="B", cost_center=cost_center, manager=person)
    EngagementUndertakingAssignment(
        engagement=engagement,
        undertaking=undertaking_a,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
        percentage=0.6,
    ).save()
    EngagementUndertakingAssignment(
        engagement=engagement,
        undertaking=undertaking_b,
        start_date=date(2024, 1, 2),
        end_date=date(2024, 1, 2),
        percentage=0.2,
    ).save()
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
    undertaking_c = Undertaking.objects.create(id=3, name="C", cost_center=cost_center, manager=person)
    EngagementUndertakingAssignment(
        engagement=engagement,
        undertaking=undertaking_c,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 1),
        percentage=0.5,
    ).save()

    with pytest.raises(CoverageOverAllocationError):
        engagement_cost_coverage(engagement)
