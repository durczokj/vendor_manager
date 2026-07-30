"""Unit tests for dashboards.services.build_summary.

Covers:
- Four filter dimensions: class_, granularity, date_range, entity_selection
- Three roles: admin, undertaking_manager, person
- Person-role isolation: a person-role user must never see another person's data.
"""

from datetime import date

import pytest
from django.contrib.auth.models import User
from rolepermissions.roles import assign_role

from companies.models import Company
from contracts.models import Contract
from dashboards.services import build_summary
from engagements.models import Engagement, EngagementOrderVersionAssignment, EngagementUndertakingAssignment
from orders.models import Order, OrderVersion
from people.models import Person
from undertakings.models import CostCenter, Undertaking

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def summary_data(db):
    """Create a minimal but complete dataset for summary tests.

    Layout:
    - company / order / contract / order_version (2024-01-01 → 2024-12-31)
    - cost_center / undertaking managed by manager_person
    - person_a (linked to person_user) — daily_rate=100, fte=1, 2 days
    - person_b (no user link, blocked from person_user) — daily_rate=200, fte=1, 2 days
    - Both engagements are fully covered by the undertaking (100 %)
    """
    # Users
    admin_user = User.objects.create_user(username="admin_user")
    manager_user = User.objects.create_user(username="manager_user")
    person_user = User.objects.create_user(username="person_user")

    assign_role(admin_user, "admin")
    assign_role(manager_user, "undertaking_manager")
    assign_role(person_user, "person")

    # Persons
    manager_person = Person.objects.create(id="M00001", first_name="Manager", last_name="User", user=manager_user)
    person_a = Person.objects.create(id="A00001", first_name="Alice", last_name="Alpha", user=person_user)
    person_b = Person.objects.create(id="B00001", first_name="Bob", last_name="Beta")

    # Company / order / contract
    company = Company.objects.create(id=9001, name="Acme Corp", email="acme@example.com")
    order = Order.objects.create(id=8001, name="Order 8001", company=company)
    contract = Contract.objects.create(id=7001, name="Contract 7001", status="active", size=1)
    order_version = OrderVersion.objects.create(
        order=order,
        contract=contract,
        version_number=1,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
    )

    # Undertaking
    cost_center = CostCenter.objects.create(id=6001, name="CC-6001")
    undertaking = Undertaking.objects.create(
        id=5001, name="Undertaking 5001", cost_center=cost_center, manager=manager_person
    )

    # Engagement A — person_a, 2 active days: 2024-01-01 / 2024-01-02
    eng_a = Engagement.objects.create(
        person=person_a,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
        daily_rate=100,
        fte=1,
    )
    EngagementOrderVersionAssignment(engagement=eng_a, order_version=order_version).save()
    EngagementUndertakingAssignment(
        engagement=eng_a,
        undertaking=undertaking,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
        percentage=1,
    ).save()

    # Engagement B — person_b, 2 active days: 2024-01-01 / 2024-01-02
    eng_b = Engagement.objects.create(
        person=person_b,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
        daily_rate=200,
        fte=1,
    )
    EngagementOrderVersionAssignment(engagement=eng_b, order_version=order_version).save()
    EngagementUndertakingAssignment(
        engagement=eng_b,
        undertaking=undertaking,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
        percentage=1,
    ).save()

    return {
        "admin_user": admin_user,
        "manager_user": manager_user,
        "person_user": person_user,
        "person_a": person_a,
        "person_b": person_b,
        "manager_person": manager_person,
        "company": company,
        "order": order,
        "order_version": order_version,
        "undertaking": undertaking,
        "eng_a": eng_a,
        "eng_b": eng_b,
    }


# ── Role tests ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_admin_sees_all_persons(summary_data):
    """Admin role returns costs for every person in the database."""
    payload = build_summary(
        summary_data["admin_user"],
        class_="Person",
        granularity="Total",
        date_range=(None, None),
        entity_selection={},
    )

    assert payload["class_"] == "Person"
    assert payload["granularity"] == "Total"
    person_ids = {row["id"] for row in payload["rows"]}
    assert "A00001" in person_ids
    assert "B00001" in person_ids


@pytest.mark.django_db
def test_undertaking_manager_sees_persons_in_managed_undertakings(summary_data):
    """An undertaking_manager sees only persons whose engagements belong to their undertakings."""
    payload = build_summary(
        summary_data["manager_user"],
        class_="Person",
        granularity="Total",
        date_range=(None, None),
        entity_selection={},
    )

    person_ids = {row["id"] for row in payload["rows"]}
    # Both engagements are in the manager's undertaking
    assert "A00001" in person_ids
    assert "B00001" in person_ids


@pytest.mark.django_db
def test_person_role_sees_only_own_person(summary_data):
    """A person-role user's summary for class_='Person' contains only their own person."""
    payload = build_summary(
        summary_data["person_user"],
        class_="Person",
        granularity="Total",
        date_range=(None, None),
        entity_selection={},
    )

    person_ids = {row["id"] for row in payload["rows"]}
    assert "A00001" in person_ids
    assert "B00001" not in person_ids, "person-role user must not see another person's data"


@pytest.mark.django_db
def test_person_role_cost_total_matches_own_engagement_only(summary_data):
    """The total cost for a person-role user equals only their own engagement cost."""
    payload = build_summary(
        summary_data["person_user"],
        class_="Person",
        granularity="Total",
        date_range=(None, None),
        entity_selection={},
    )

    rows = {row["id"]: row["cost"] for row in payload["rows"]}
    # person_a: 2 days × 100 rate × 1.0 fte = 200
    assert rows["A00001"] == pytest.approx(200.0)
    # person_b must not appear at all
    assert "B00001" not in rows


@pytest.mark.django_db
def test_person_role_entity_selection_other_person_returns_no_data(summary_data):
    """A person-role user filtering by another person's ID receives no rows."""
    payload = build_summary(
        summary_data["person_user"],
        class_="Person",
        granularity="Total",
        date_range=(None, None),
        entity_selection={"Person": ["B00001"]},  # B00001 is not accessible to person_user
    )

    assert payload["rows"] == []


# ── Class_ filter tests ───────────────────────────────────────────────────────


@pytest.mark.django_db
def test_class_undertaking_groups_by_undertaking(summary_data):
    """class_='Undertaking' groups costs by undertaking."""
    payload = build_summary(
        summary_data["admin_user"],
        class_="Undertaking",
        granularity="Total",
        date_range=(None, None),
        entity_selection={},
    )

    assert payload["class_"] == "Undertaking"
    undertaking_ids = {row["id"] for row in payload["rows"]}
    assert summary_data["undertaking"].id in undertaking_ids


@pytest.mark.django_db
def test_class_order_groups_by_order(summary_data):
    """class_='Order' groups costs by order."""
    payload = build_summary(
        summary_data["admin_user"],
        class_="Order",
        granularity="Total",
        date_range=(None, None),
        entity_selection={},
    )

    assert payload["class_"] == "Order"
    order_ids = {row["id"] for row in payload["rows"]}
    assert summary_data["order"].id in order_ids


@pytest.mark.django_db
def test_class_company_groups_by_company(summary_data):
    """class_='Company' groups costs by company."""
    payload = build_summary(
        summary_data["admin_user"],
        class_="Company",
        granularity="Total",
        date_range=(None, None),
        entity_selection={},
    )

    assert payload["class_"] == "Company"
    company_ids = {row["id"] for row in payload["rows"]}
    assert summary_data["company"].id in company_ids


@pytest.mark.django_db
def test_class_engagement_groups_by_engagement(summary_data):
    """class_='Engagement' groups costs by engagement."""
    payload = build_summary(
        summary_data["admin_user"],
        class_="Engagement",
        granularity="Total",
        date_range=(None, None),
        entity_selection={},
    )

    assert payload["class_"] == "Engagement"
    engagement_ids = {row["id"] for row in payload["rows"]}
    assert summary_data["eng_a"].id in engagement_ids
    assert summary_data["eng_b"].id in engagement_ids


# ── Granularity tests ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_granularity_total_has_no_time_bucket(summary_data):
    """Total granularity rows have date=None and month=None."""
    payload = build_summary(
        summary_data["admin_user"],
        class_="Person",
        granularity="Total",
        date_range=(None, None),
        entity_selection={},
    )

    for row in payload["rows"]:
        assert row["date"] is None
        assert row["month"] is None


@pytest.mark.django_db
def test_granularity_daily_has_date_field(summary_data):
    """Daily granularity rows have a non-None date in ISO format."""
    payload = build_summary(
        summary_data["admin_user"],
        class_="Person",
        granularity="Daily",
        date_range=(None, None),
        entity_selection={},
    )

    assert payload["granularity"] == "Daily"
    for row in payload["rows"]:
        assert row["date"] is not None
        assert row["month"] is None
        # Should be a valid ISO date string like "2024-01-01"
        date.fromisoformat(row["date"])


@pytest.mark.django_db
def test_granularity_monthly_has_month_field(summary_data):
    """Monthly granularity rows have a non-None month in YYYY-MM format."""
    payload = build_summary(
        summary_data["admin_user"],
        class_="Person",
        granularity="Monthly",
        date_range=(None, None),
        entity_selection={},
    )

    assert payload["granularity"] == "Monthly"
    for row in payload["rows"]:
        assert row["month"] is not None
        assert row["date"] is None
        # Should be YYYY-MM format
        assert len(row["month"]) == 7
        assert row["month"][4] == "-"


@pytest.mark.django_db
def test_granularity_total_cost_equals_sum_of_daily_costs(summary_data):
    """Total cost for a person equals the sum of their daily costs."""
    daily_payload = build_summary(
        summary_data["admin_user"],
        class_="Person",
        granularity="Daily",
        date_range=(None, None),
        entity_selection={},
    )
    total_payload = build_summary(
        summary_data["admin_user"],
        class_="Person",
        granularity="Total",
        date_range=(None, None),
        entity_selection={},
    )

    daily_sums: dict[str, float] = {}
    for row in daily_payload["rows"]:
        pid = row["id"]
        daily_sums[pid] = daily_sums.get(pid, 0.0) + row["cost"]

    total_map = {row["id"]: row["cost"] for row in total_payload["rows"]}
    for pid, expected in daily_sums.items():
        assert total_map[pid] == pytest.approx(expected)


# ── Date-range filter tests ───────────────────────────────────────────────────


@pytest.mark.django_db
def test_date_range_min_date_excludes_earlier_rows(summary_data):
    """min_date filter excludes days before the given date."""
    # Without filter: 2 days (2024-01-01 and 2024-01-02)
    full_payload = build_summary(
        summary_data["admin_user"],
        class_="Person",
        granularity="Daily",
        date_range=(None, None),
        entity_selection={},
    )
    full_dates = {row["date"] for row in full_payload["rows"]}
    assert "2024-01-01" in full_dates

    # With min_date=2024-01-02: only 2024-01-02 remains
    filtered_payload = build_summary(
        summary_data["admin_user"],
        class_="Person",
        granularity="Daily",
        date_range=(date(2024, 1, 2), None),
        entity_selection={},
    )
    filtered_dates = {row["date"] for row in filtered_payload["rows"]}
    assert "2024-01-01" not in filtered_dates
    assert "2024-01-02" in filtered_dates


@pytest.mark.django_db
def test_date_range_max_date_excludes_later_rows(summary_data):
    """max_date filter excludes days after the given date."""
    filtered_payload = build_summary(
        summary_data["admin_user"],
        class_="Person",
        granularity="Daily",
        date_range=(None, date(2024, 1, 1)),
        entity_selection={},
    )
    filtered_dates = {row["date"] for row in filtered_payload["rows"]}
    assert "2024-01-02" not in filtered_dates
    assert "2024-01-01" in filtered_dates


@pytest.mark.django_db
def test_date_range_outside_engagement_returns_no_rows(summary_data):
    """A date range entirely outside the engagement period returns an empty payload."""
    payload = build_summary(
        summary_data["admin_user"],
        class_="Person",
        granularity="Total",
        date_range=(date(2025, 1, 1), date(2025, 1, 31)),
        entity_selection={},
    )

    # The engagements end on 2024-01-02; no active costs in 2025
    assert payload["rows"] == [] or all(row["cost"] == 0.0 for row in payload["rows"])


# ── Entity selection filter tests ─────────────────────────────────────────────


@pytest.mark.django_db
def test_entity_selection_filters_to_single_person(summary_data):
    """entity_selection={'Person': [person_a.id]} returns only person_a."""
    payload = build_summary(
        summary_data["admin_user"],
        class_="Person",
        granularity="Total",
        date_range=(None, None),
        entity_selection={"Person": [summary_data["person_a"].id]},
    )

    person_ids = {row["id"] for row in payload["rows"]}
    assert "A00001" in person_ids
    assert "B00001" not in person_ids


@pytest.mark.django_db
def test_entity_selection_filters_by_undertaking(summary_data):
    """entity_selection={'Undertaking': [undertaking.id]} limits to costs under that undertaking."""
    payload = build_summary(
        summary_data["admin_user"],
        class_="Undertaking",
        granularity="Total",
        date_range=(None, None),
        entity_selection={"Undertaking": [summary_data["undertaking"].id]},
    )

    undertaking_ids = {row["id"] for row in payload["rows"]}
    assert summary_data["undertaking"].id in undertaking_ids


@pytest.mark.django_db
def test_entity_selection_empty_list_means_all(summary_data):
    """An empty list for a class means 'no restriction' — all accessible data is returned."""
    payload_no_filter = build_summary(
        summary_data["admin_user"],
        class_="Person",
        granularity="Total",
        date_range=(None, None),
        entity_selection={},
    )
    payload_empty_list = build_summary(
        summary_data["admin_user"],
        class_="Person",
        granularity="Total",
        date_range=(None, None),
        entity_selection={"Person": []},
    )

    ids_no_filter = {row["id"] for row in payload_no_filter["rows"]}
    ids_empty_list = {row["id"] for row in payload_empty_list["rows"]}
    assert ids_no_filter == ids_empty_list


# ── Validation tests ──────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_invalid_class_raises_value_error(summary_data):
    """build_summary raises ValueError for an unknown class_."""
    with pytest.raises(ValueError, match="Invalid class_"):
        build_summary(
            summary_data["admin_user"],
            class_="Unknown",
            granularity="Total",
            date_range=(None, None),
            entity_selection={},
        )


@pytest.mark.django_db
def test_invalid_granularity_raises_value_error(summary_data):
    """build_summary raises ValueError for an unknown granularity."""
    with pytest.raises(ValueError, match="Invalid granularity"):
        build_summary(
            summary_data["admin_user"],
            class_="Person",
            granularity="Yearly",
            date_range=(None, None),
            entity_selection={},
        )
