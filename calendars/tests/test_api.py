"""Tests for the calendars REST API — admin-only access."""

from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from rolepermissions.roles import assign_role

from calendars.models import (
    MON_FRI_MASK,
    Calendar,
    CalendarAssignment,
    HolidayCalendar,
    WeeklyPattern,
)
from calendars.tests.factories import (
    CalendarAssignmentFactory,
    CalendarFactory,
    HolidayCalendarFactory,
    WeeklyPatternFactory,
)
from people.tests.factories import PersonFactory

LIST_URLS = [
    "api-v1:weekly-patterns-list",
    "api-v1:holiday-calendars-list",
    "api-v1:calendars-list",
    "api-v1:calendar-assignments-list",
]


def _login(client: Client, username: str, role: str) -> User:
    user = User.objects.create_user(username, None, "pw")
    assign_role(user, role)
    PersonFactory(id=username[:6].upper().ljust(6, "X"), user=user)
    client.force_login(user)
    return user


# ─── Auth / anon ────────────────────────────────────────────────────────────


@pytest.mark.parametrize("url_name", LIST_URLS)
@pytest.mark.django_db
def test_anonymous_gets_401_or_403_on_list(url_name: str) -> None:
    """Unauthenticated clients cannot list any calendar resource."""
    response = Client().get(reverse(url_name))
    assert response.status_code in {401, 403}


# ─── Role gating ────────────────────────────────────────────────────────────


@pytest.mark.parametrize("url_name", LIST_URLS)
@pytest.mark.django_db
def test_person_role_denied(url_name: str) -> None:
    """Non-admin authenticated users are denied."""
    client = Client()
    _login(client, "plain1", "person")
    response = client.get(reverse(url_name))
    assert response.status_code == 403


@pytest.mark.parametrize("url_name", LIST_URLS)
@pytest.mark.django_db
def test_admin_role_allowed(url_name: str) -> None:
    """Admins can list every calendar resource."""
    client = Client()
    _login(client, "admin1", "admin")
    response = client.get(reverse(url_name))
    assert response.status_code == 200


# ─── CRUD ───────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_admin_can_create_weekly_pattern() -> None:
    """POSTing to ``weekly-patterns-list`` creates a pattern."""
    client = Client()
    _login(client, "admin2", "admin")
    response = client.post(
        reverse("api-v1:weekly-patterns-list"),
        data={"name": "Mon-Fri", "working_days": MON_FRI_MASK},
        content_type="application/json",
    )
    assert response.status_code == 201
    assert WeeklyPattern.objects.filter(name="Mon-Fri").exists()


@pytest.mark.django_db
def test_admin_can_create_holiday_calendar() -> None:
    """POSTing to ``holiday-calendars-list`` creates a holiday calendar."""
    client = Client()
    _login(client, "admin3", "admin")
    response = client.post(
        reverse("api-v1:holiday-calendars-list"),
        data={"name": "PL public", "country_code": "PL", "subdivision": ""},
        content_type="application/json",
    )
    assert response.status_code == 201
    assert HolidayCalendar.objects.filter(name="PL public").exists()


@pytest.mark.django_db
def test_admin_can_create_calendar() -> None:
    """POSTing to ``calendars-list`` creates a calendar from existing FKs."""
    client = Client()
    _login(client, "admin4", "admin")
    pattern = WeeklyPatternFactory(name="P1")
    hc = HolidayCalendarFactory(name="HC1")
    response = client.post(
        reverse("api-v1:calendars-list"),
        data={"name": "C1", "weekly_pattern": pattern.pk, "holiday_calendar": hc.pk},
        content_type="application/json",
    )
    assert response.status_code == 201
    created = Calendar.objects.get(name="C1")
    assert created.weekly_pattern_id == pattern.pk
    assert created.holiday_calendar_id == hc.pk


@pytest.mark.django_db
def test_admin_can_delete_calendar() -> None:
    """DELETE removes a calendar."""
    client = Client()
    _login(client, "admin5", "admin")
    calendar = CalendarFactory(name="doomed")
    response = client.delete(reverse("api-v1:calendars-detail", args=[calendar.pk]))
    assert response.status_code == 204
    assert not Calendar.objects.filter(pk=calendar.pk).exists()


@pytest.mark.django_db
def test_person_cannot_create_calendar() -> None:
    """Non-admin authenticated users cannot POST to the calendars list."""
    client = Client()
    _login(client, "plain2", "person")
    pattern = WeeklyPatternFactory(name="P2")
    hc = HolidayCalendarFactory(name="HC2")
    response = client.post(
        reverse("api-v1:calendars-list"),
        data={"name": "nope", "weekly_pattern": pattern.pk, "holiday_calendar": hc.pk},
        content_type="application/json",
    )
    assert response.status_code == 403
    assert not Calendar.objects.filter(name="nope").exists()


# ─── CalendarAssignment endpoints ────────────────────────────────────────────


@pytest.mark.django_db
def test_admin_can_create_calendar_assignment() -> None:
    """POSTing a valid CalendarAssignment succeeds."""
    client = Client()
    _login(client, "admin6", "admin")
    person = PersonFactory(id="A00099")
    calendar = CalendarFactory(name="C-assign")
    response = client.post(
        reverse("api-v1:calendar-assignments-list"),
        data={
            "person": person.pk,
            "calendar": calendar.pk,
            "start_date": "2026-01-01",
            "end_date": "2026-06-30",
        },
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    assert CalendarAssignment.objects.filter(person=person, calendar=calendar).exists()


@pytest.mark.django_db
def test_admin_can_create_open_ended_assignment() -> None:
    """Open-ended assignments (no ``end_date``) are accepted."""
    client = Client()
    _login(client, "admin7", "admin")
    person = PersonFactory(id="A00100")
    calendar = CalendarFactory(name="C-open")
    response = client.post(
        reverse("api-v1:calendar-assignments-list"),
        data={
            "person": person.pk,
            "calendar": calendar.pk,
            "start_date": "2026-01-01",
            "end_date": None,
        },
        content_type="application/json",
    )
    assert response.status_code == 201, response.content


@pytest.mark.django_db
def test_overlapping_assignment_rejected() -> None:
    """POSTing an overlapping assignment returns 400."""
    client = Client()
    _login(client, "admin8", "admin")
    person = PersonFactory(id="A00101")
    calendar = CalendarFactory(name="C-overlap")
    CalendarAssignmentFactory(
        person=person,
        calendar=calendar,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 6, 30),
    )
    response = client.post(
        reverse("api-v1:calendar-assignments-list"),
        data={
            "person": person.pk,
            "calendar": calendar.pk,
            "start_date": "2026-06-15",
            "end_date": "2026-12-31",
        },
        content_type="application/json",
    )
    assert response.status_code == 400
    assert CalendarAssignment.objects.filter(person=person).count() == 1


@pytest.mark.django_db
def test_person_role_cannot_create_calendar_assignment() -> None:
    """Non-admin users get 403 on the calendar-assignments endpoint."""
    client = Client()
    _login(client, "plain3", "person")
    person = PersonFactory(id="A00102")
    calendar = CalendarFactory(name="C-denied")
    response = client.post(
        reverse("api-v1:calendar-assignments-list"),
        data={
            "person": person.pk,
            "calendar": calendar.pk,
            "start_date": "2026-01-01",
            "end_date": "2026-06-30",
        },
        content_type="application/json",
    )
    assert response.status_code == 403
    assert not CalendarAssignment.objects.filter(person=person).exists()


# ─── Undertaking Manager scope ──────────────────────────────────────────────


@pytest.mark.django_db
def test_um_can_list_all_calendar_resources() -> None:
    """Undertaking Managers hold read access on all four list endpoints."""
    client = Client()
    _login(client, "umgr1", "undertaking_manager")
    for url_name in LIST_URLS:
        response = client.get(reverse(url_name))
        assert response.status_code == 200, url_name


@pytest.mark.django_db
def test_um_cannot_create_calendar() -> None:
    """UMs cannot create the shared Calendar / HolidayCalendar / WeeklyPattern templates."""
    client = Client()
    _login(client, "umgr2", "undertaking_manager")
    pattern = WeeklyPatternFactory(name="P-um")
    hc = HolidayCalendarFactory(name="HC-um")
    response = client.post(
        reverse("api-v1:calendars-list"),
        data={"name": "um-nope", "weekly_pattern": pattern.pk, "holiday_calendar": hc.pk},
        content_type="application/json",
    )
    assert response.status_code == 403
    assert not Calendar.objects.filter(name="um-nope").exists()


@pytest.mark.django_db
def test_um_can_assign_person_in_their_scope() -> None:
    """UM can POST a CalendarAssignment for a person under an undertaking they manage."""
    from engagements.tests.factories import (
        EngagementFactory,
        EngagementUndertakingAssignmentFactory,
    )
    from undertakings.tests.factories import CostCenterFactory, UndertakingFactory

    client = Client()
    um_user = _login(client, "umgr3", "undertaking_manager")
    um_person = um_user.person
    cc = CostCenterFactory(id=6100, name="CC-um3")
    undertaking = UndertakingFactory(id=5100, name="U-um3", cost_center=cc, manager=um_person)

    assigned_person = PersonFactory(id="A00103")
    engagement = EngagementFactory(person=assigned_person, start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    EngagementUndertakingAssignmentFactory(
        engagement=engagement,
        undertaking=undertaking,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )

    calendar = CalendarFactory(name="C-um3")
    response = client.post(
        reverse("api-v1:calendar-assignments-list"),
        data={
            "person": assigned_person.pk,
            "calendar": calendar.pk,
            "start_date": "2026-01-01",
            "end_date": "2026-06-30",
        },
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    assert CalendarAssignment.objects.filter(person=assigned_person).exists()


@pytest.mark.django_db
def test_um_cannot_assign_person_outside_their_scope() -> None:
    """UM POST to a person not connected to any of their undertakings returns 403."""
    client = Client()
    _login(client, "umgr4", "undertaking_manager")

    stranger = PersonFactory(id="A00104")
    calendar = CalendarFactory(name="C-um4")
    response = client.post(
        reverse("api-v1:calendar-assignments-list"),
        data={
            "person": stranger.pk,
            "calendar": calendar.pk,
            "start_date": "2026-01-01",
            "end_date": "2026-06-30",
        },
        content_type="application/json",
    )
    assert response.status_code == 403
    assert not CalendarAssignment.objects.filter(person=stranger).exists()
