"""UI smoke tests.

Guards against the class of regression introduced by P4 where the shared
_form.html template silently no-op'd every create flow (nested crispy
<form> inside the outer <form>). Every list/create GET must render, and
POSTing a valid form to a create endpoint must persist an object and
redirect (302 or 303) — not return 200 with an unposted form.

Kept intentionally boring: exercises the URL wiring + template chain
only. It does not attempt full field-level validation of every model.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from rolepermissions.roles import assign_role

from companies.models import Company
from contracts.models import Contract
from engagements.models import Engagement
from orders.models import Order, OrderVersion
from people.models import Person
from undertakings.models import CostCenter, Undertaking


@pytest.fixture
def admin_client(db) -> Client:
    """Return a Client logged in as an admin-role user."""
    user = User.objects.create_user(username="ui-admin", password="x")
    assign_role(user, "admin")
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def seed_for_forms(db) -> dict:
    """Minimal object graph so create-form POSTs have valid FK targets."""
    cc = CostCenter.objects.create(id=9001, name="UI CC")
    manager = Person.objects.create(id="900001", first_name="UI", last_name="Manager")
    undertaking = Undertaking.objects.create(id=9101, name="UI Undertaking", cost_center=cc, manager=manager)
    company = Company.objects.create(id=9201, name="UI Company", email="ui@example.com")
    contract = Contract.objects.create(id=9301, name="UI Contract", status="active", size=1)
    order = Order.objects.create(id=9401, name="UI Order", company=company)
    order_version = OrderVersion.objects.create(
        order=order,
        contract=contract,
        version_number=1,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
    )
    person = Person.objects.create(id="900002", first_name="UI", last_name="Person")
    engagement = Engagement.objects.create(
        person=person,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        daily_rate=100,
        fte=1,
    )
    return {
        "cost_center": cc,
        "manager": manager,
        "undertaking": undertaking,
        "company": company,
        "contract": contract,
        "order": order,
        "order_version": order_version,
        "person": person,
        "engagement": engagement,
    }


LIST_URL_NAMES = [
    "person-list",
    "company-list",
    "undertaking-list",
    "engagement-list",
    "engagement-undertaking-assignment-list",
    "engagement-order-version-assignment-list",
    "leave-list",
    "contract-list",
    "order-list",
]


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", LIST_URL_NAMES)
def test_list_pages_render(admin_client: Client, url_name: str) -> None:
    """Every registered list URL renders 200 for an admin."""
    response = admin_client.get(reverse(url_name))
    assert response.status_code == 200, f"{url_name} returned {response.status_code}"


CREATE_URL_NAMES = [
    "person-create",
    "company-create",
    "undertaking-create",
    "engagement-create",
    "engagement-undertaking-assignment-create",
    "engagement-order-version-assignment-create",
    "leave-create",
    "contract-create",
    "order-create",
]


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", CREATE_URL_NAMES)
def test_create_pages_render_a_real_form(admin_client: Client, url_name: str) -> None:
    """Create GETs must render a <form> with a CSRF token and enough <input>s.

    Regression guard: P4 introduced a nested-form bug where the outer
    <form> ended up empty. This test asserts there are at least two
    <input> tags (CSRF + something) so we can never silently ship a
    create page with no posted fields again.
    """
    response = admin_client.get(reverse(url_name))
    assert response.status_code == 200
    body = response.content.decode("utf-8", errors="replace")
    assert "<form" in body
    assert "csrfmiddlewaretoken" in body
    input_count = body.count("<input")
    assert input_count >= 2, f"{url_name} has only {input_count} <input> tags"


@pytest.mark.django_db
def test_undertaking_assignment_create_persists(admin_client: Client, seed_for_forms: dict) -> None:
    """POSTing a valid EngagementUndertakingAssignment form must redirect."""
    from engagements.models import EngagementUndertakingAssignment

    before = EngagementUndertakingAssignment.objects.count()
    response = admin_client.post(
        reverse("engagement-undertaking-assignment-create"),
        data={
            "engagement": seed_for_forms["engagement"].pk,
            "undertaking": seed_for_forms["undertaking"].pk,
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "percentage": "1.00",
        },
    )
    assert response.status_code in (302, 303), (
        f"expected redirect, got {response.status_code}: {response.content[:400]!r}"
    )
    assert EngagementUndertakingAssignment.objects.count() == before + 1


@pytest.mark.django_db
def test_company_create_persists(admin_client: Client) -> None:
    """POSTing a valid Company form must redirect and create the row."""
    before = Company.objects.count()
    response = admin_client.post(
        reverse("company-create"),
        data={
            "id": 9501,
            "name": "Smoke Company",
            "email": "smoke@example.com",
        },
    )
    assert response.status_code in (302, 303), (
        f"expected redirect, got {response.status_code}: {response.content[:400]!r}"
    )
    assert Company.objects.count() == before + 1


@pytest.mark.django_db
def test_leave_create_persists(admin_client: Client, seed_for_forms: dict) -> None:
    """POSTing a valid Leave form must redirect and create the row."""
    from leaves.models import Leave

    before = Leave.objects.count()
    response = admin_client.post(
        reverse("leave-create"),
        data={
            "person": seed_for_forms["person"].pk,
            "start_date": "2025-02-01",
            "end_date": "2025-02-05",
            "percentage": Decimal("0.50"),
        },
    )
    assert response.status_code in (302, 303), (
        f"expected redirect, got {response.status_code}: {response.content[:400]!r}"
    )
    assert Leave.objects.count() == before + 1


@pytest.mark.django_db
def test_leave_list_page_has_working_add_form_and_month_picker(admin_client: Client, seed_for_forms: dict) -> None:
    """The leaves list page must render an inline add form with real fields and a month picker."""
    response = admin_client.get(reverse("leave-list"))
    assert response.status_code == 200
    body = response.content.decode("utf-8", errors="replace")
    # Inline add-leave form is present with the person select and submit button.
    assert 'action="/leaves/create/"' in body
    assert 'name="person"' in body
    assert 'name="percentage"' in body
    # Month picker is present so the user can navigate months on the calendar.
    assert 'name="month"' in body
    assert 'name="year"' in body


@pytest.mark.django_db
def test_order_detail_shows_add_version_button(admin_client: Client, seed_for_forms: dict) -> None:
    """The order detail page must expose an Add button for the nested Versions block."""
    response = admin_client.get(reverse("order-detail", kwargs={"pk": seed_for_forms["order"].pk}))
    assert response.status_code == 200
    body = response.content.decode("utf-8", errors="replace")
    assert reverse("order-version-create") in body


@pytest.mark.django_db
def test_engagement_detail_shows_add_undertaking_assignment_button(admin_client: Client, seed_for_forms: dict) -> None:
    """The engagement detail page must expose an Add button for the nested Assignments block."""
    response = admin_client.get(reverse("engagement-detail", kwargs={"pk": seed_for_forms["engagement"].pk}))
    assert response.status_code == 200
    body = response.content.decode("utf-8", errors="replace")
    assert reverse("engagement-undertaking-assignment-create") in body


@pytest.mark.django_db
def test_undertaking_detail_linkifies_fk_fields(admin_client: Client, seed_for_forms: dict) -> None:
    """Undertaking detail: Manager FK value must be an <a href="/people/…/">…</a>.

    Regression: previously the detail template rendered FK values as plain text
    (or as "CostCenter object (id)" when __str__ was missing).
    """
    response = admin_client.get(reverse("undertaking-detail", kwargs={"pk": seed_for_forms["undertaking"].pk}))
    assert response.status_code == 200
    body = response.content.decode("utf-8", errors="replace")
    manager_url = reverse("person-detail", kwargs={"pk": seed_for_forms["manager"].pk})
    assert f'<a href="{manager_url}">' in body
    # Cost centers now have a __str__ that returns their name.
    assert "CostCenter object" not in body
    assert seed_for_forms["cost_center"].name in body


@pytest.mark.django_db
def test_engagement_detail_nested_undertaking_assignment_has_edit_and_delete(
    admin_client: Client,
    seed_for_forms: dict,
) -> None:
    """Nested Assignments row must render Edit + Delete buttons for admin.

    Regression: TemplateColumn on the nested table couldn't see `table` in the
    outer detail-view context, so `{% if table.can_manage %}` evaluated False
    and the Actions cell rendered empty.
    """
    from engagements.models import EngagementUndertakingAssignment

    assignment = EngagementUndertakingAssignment.objects.create(
        engagement=seed_for_forms["engagement"],
        undertaking=seed_for_forms["undertaking"],
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        percentage=Decimal("1.00"),
    )
    response = admin_client.get(reverse("engagement-detail", kwargs={"pk": seed_for_forms["engagement"].pk}))
    assert response.status_code == 200
    body = response.content.decode("utf-8", errors="replace")
    assert reverse("engagement-undertaking-assignment-update", kwargs={"pk": assignment.pk}) in body
    assert reverse("engagement-undertaking-assignment-delete", kwargs={"pk": assignment.pk}) in body


@pytest.mark.django_db
def test_table_header_link_css_present() -> None:
    """table_styles.css must style header sort links white with no underline."""
    from pathlib import Path

    css = Path("staticfiles/table_styles.css").read_text()
    assert "table th a" in css
    # White colour + no underline for the sort links.
    assert "color: white" in css
    assert "text-decoration: none" in css
