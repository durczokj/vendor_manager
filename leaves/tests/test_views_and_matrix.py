"""Tests for leaves list view: undertaking filter and matrix view mode."""

from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from rolepermissions.roles import assign_role

from companies.models import Company
from contracts.models import Contract
from engagements.models import Engagement, EngagementUndertakingAssignment
from leaves.models import Leave
from leaves.utils.leave_matrix import LeaveMatrix
from orders.models import Order, OrderVersion
from people.models import Person
from undertakings.models import CostCenter, Undertaking


@pytest.fixture
def admin_client(db) -> Client:
    """Return a Django Client logged in as an admin-role user."""
    user = User.objects.create_user(username="leaves-admin", password="x")
    assign_role(user, "admin")
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def two_people_two_undertakings(db) -> dict:
    """Two people, each assigned to their own undertaking, each with a leave in March 2025."""
    manager = Person.objects.create(id="M00001", first_name="M", last_name="Boss")
    cc = CostCenter.objects.create(id=8001, name="CC")
    u_alpha = Undertaking.objects.create(id=8101, name="Alpha", cost_center=cc, manager=manager)
    u_beta = Undertaking.objects.create(id=8102, name="Beta", cost_center=cc, manager=manager)
    company = Company.objects.create(id=8201, name="Co", email="c@example.com")
    Contract.objects.create(id=8301, name="Con", status="active", size=1)
    order = Order.objects.create(id=8401, name="Ord", company=company)
    OrderVersion.objects.create(
        order=order,
        contract_id=8301,
        version_number=1,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
    )

    alice = Person.objects.create(id="A00001", first_name="Alice", last_name="A")
    bob = Person.objects.create(id="B00001", first_name="Bob", last_name="B")

    eng_alice = Engagement.objects.create(
        person=alice, start_date=date(2025, 1, 1), end_date=date(2025, 12, 31), daily_rate=100, fte=1
    )
    eng_bob = Engagement.objects.create(
        person=bob, start_date=date(2025, 1, 1), end_date=date(2025, 12, 31), daily_rate=100, fte=1
    )
    EngagementUndertakingAssignment.objects.create(
        engagement=eng_alice,
        undertaking=u_alpha,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        percentage="1.00",
    )
    EngagementUndertakingAssignment.objects.create(
        engagement=eng_bob,
        undertaking=u_beta,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        percentage="1.00",
    )

    Leave.objects.create(person=alice, start_date=date(2025, 3, 3), end_date=date(2025, 3, 5), percentage="1.00")
    Leave.objects.create(person=bob, start_date=date(2025, 3, 10), end_date=date(2025, 3, 12), percentage="0.50")

    return {"alice": alice, "bob": bob, "u_alpha": u_alpha, "u_beta": u_beta}


@pytest.mark.django_db
def test_undertaking_filter_narrows_leaves_to_assigned_people(
    admin_client: Client, two_people_two_undertakings: dict
) -> None:
    """?undertaking=<pk> should keep only people assigned to that undertaking."""
    u_alpha = two_people_two_undertakings["u_alpha"]
    alice = two_people_two_undertakings["alice"]
    bob = two_people_two_undertakings["bob"]

    response = admin_client.get(reverse("leave-list"), {"year": 2025, "month": 3, "undertaking": u_alpha.pk})

    assert response.status_code == 200
    people_in_result = {leave.person_id for leave in response.context["object_list"]}
    assert alice.pk in people_in_result
    assert bob.pk not in people_in_result


@pytest.mark.django_db
def test_undertaking_filter_absent_shows_all(admin_client: Client, two_people_two_undertakings: dict) -> None:
    """Omitting ?undertaking must return everyone's leaves."""
    alice = two_people_two_undertakings["alice"]
    bob = two_people_two_undertakings["bob"]

    response = admin_client.get(reverse("leave-list"), {"year": 2025, "month": 3})

    assert response.status_code == 200
    people_in_result = {leave.person_id for leave in response.context["object_list"]}
    assert alice.pk in people_in_result
    assert bob.pk in people_in_result


@pytest.mark.django_db
def test_matrix_view_renders_table(admin_client: Client, two_people_two_undertakings: dict) -> None:
    """?view=matrix must render the leave-matrix table."""
    response = admin_client.get(reverse("leave-list"), {"year": 2025, "month": 3, "view": "matrix"})

    assert response.status_code == 200
    body = response.content.decode("utf-8")
    assert 'class="leave-matrix"' in body
    # Header contains days 1..31 for March.
    assert "<th>1</th>" in body
    assert "<th>31</th>" in body
    # Undertaking dropdown is present.
    assert 'name="undertaking"' in body
    # View selector is present.
    assert 'name="view"' in body


@pytest.mark.django_db
def test_calendar_is_default_view(admin_client: Client, two_people_two_undertakings: dict) -> None:
    """No ?view param → calendar view (regression guard)."""
    response = admin_client.get(reverse("leave-list"), {"year": 2025, "month": 3})

    assert response.status_code == 200
    body = response.content.decode("utf-8")
    assert 'class="calendar"' in body
    assert 'class="leave-matrix"' not in body


@pytest.mark.django_db
def test_invalid_view_falls_back_to_calendar(admin_client: Client) -> None:
    """Unknown ?view= values fall back to calendar without erroring."""
    response = admin_client.get(reverse("leave-list"), {"year": 2025, "month": 3, "view": "bogus"})
    assert response.status_code == 200
    assert 'class="calendar"' in response.content.decode("utf-8")


class _StubPerson:
    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self) -> str:
        return self.name


class _StubLeave:
    def __init__(self, person_name: str, start: date, end: date, pct: str) -> None:
        self.person = _StubPerson(person_name)
        self.start_date = start
        self.end_date = end
        self.percentage = pct


def test_matrix_renders_no_leaves_placeholder() -> None:
    """Rendering with an empty leaves list shows the placeholder row."""
    html = LeaveMatrix(year=2025, month=3, leaves=[]).render()
    assert "No leaves in this period." in html


def test_matrix_marks_days_covered_by_a_leave() -> None:
    """A leave from day 3–5 should produce three shaded cells for that person."""
    leaves = [_StubLeave("Alice", date(2025, 3, 3), date(2025, 3, 5), "1.00")]
    html = LeaveMatrix(year=2025, month=3, leaves=leaves).render()
    # Three cells with the percentage.
    assert html.count(">1.00<") == 3
