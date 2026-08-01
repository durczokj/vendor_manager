from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rolepermissions.roles import assign_role

from companies.models import Company
from companies.permissions import access_company
from contracts.models import Contract
from contracts.permissions import access_contract
from engagements.models import Engagement, EngagementOrderVersionAssignment, EngagementUndertakingAssignment
from engagements.permissions import (
    access_engagement,
    access_engagement_order_version_assignment,
    access_engagement_undertaking_assignment,
)
from leaves.models import Leave
from leaves.permissions import access_leave
from orders.models import Order, OrderVersion
from orders.permissions import access_order, access_order_version
from people.models import Person
from people.permissions import access_person
from undertakings.models import CostCenter, Undertaking
from undertakings.permissions import access_cost_center, access_undertaking
from vendor_manager.roles import Admin, UndertakingManager
from vendor_manager.roles import Person as PersonRole


@pytest.fixture
def seeded_access_data(db):
    admin_user = User.objects.create_user(username="admin")
    manager_user = User.objects.create_user(username="manager")
    person_user = User.objects.create_user(username="person")

    assign_role(admin_user, "admin")
    assign_role(manager_user, "undertaking_manager")
    assign_role(person_user, "person")

    manager_person = Person.objects.create(id="100001", first_name="Manager", last_name="User", user=manager_user)
    allowed_person = Person.objects.create(id="100002", first_name="Allowed", last_name="User", user=person_user)
    blocked_person = Person.objects.create(id="100003", first_name="Blocked", last_name="User")

    allowed_cost_center = CostCenter.objects.create(id=1001, name="Allowed Cost Center")
    blocked_cost_center = CostCenter.objects.create(id=1002, name="Blocked Cost Center")

    allowed_undertaking = Undertaking.objects.create(
        id=2001, name="Allowed Undertaking", cost_center=allowed_cost_center, manager=manager_person
    )
    blocked_undertaking = Undertaking.objects.create(
        id=2002, name="Blocked Undertaking", cost_center=blocked_cost_center, manager=blocked_person
    )

    allowed_company = Company.objects.create(id=3001, name="Allowed Company", email="allowed@example.com")
    blocked_company = Company.objects.create(id=3002, name="Blocked Company", email="blocked@example.com")

    allowed_order = Order.objects.create(id=4001, name="Allowed Order", company=allowed_company)
    blocked_order = Order.objects.create(id=4002, name="Blocked Order", company=blocked_company)

    allowed_contract = Contract.objects.create(id=5001, name="Allowed Contract", status="active", size=1)
    blocked_contract = Contract.objects.create(id=5002, name="Blocked Contract", status="active", size=1)

    allowed_order_version = OrderVersion.objects.create(
        order=allowed_order,
        contract=allowed_contract,
        version_number=1,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
    )
    blocked_order_version = OrderVersion.objects.create(
        order=blocked_order,
        contract=blocked_contract,
        version_number=1,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
    )

    allowed_engagement = Engagement.objects.create(
        person=allowed_person,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        daily_rate=100,
        fte=1,
    )
    blocked_engagement = Engagement.objects.create(
        person=blocked_person,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        daily_rate=100,
        fte=1,
    )

    allowed_order_assignment = EngagementOrderVersionAssignment(
        engagement=allowed_engagement, order_version=allowed_order_version
    )
    allowed_order_assignment.save()
    blocked_order_assignment = EngagementOrderVersionAssignment(
        engagement=blocked_engagement, order_version=blocked_order_version
    )
    blocked_order_assignment.save()

    allowed_undertaking_assignment = EngagementUndertakingAssignment.objects.create(
        engagement=allowed_engagement,
        undertaking=allowed_undertaking,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        percentage=Decimal("1.00"),
    )
    blocked_undertaking_assignment = EngagementUndertakingAssignment.objects.create(
        engagement=blocked_engagement,
        undertaking=blocked_undertaking,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        percentage=Decimal("1.00"),
    )

    allowed_leave = Leave.objects.create(
        person=allowed_person,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 2),
        percentage=Decimal("0.50"),
    )
    blocked_leave = Leave.objects.create(
        person=blocked_person,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 2),
        percentage=Decimal("0.50"),
    )

    return {
        "users": {
            "admin": admin_user,
            "undertaking_manager": manager_user,
            "person": person_user,
        },
        "seed_ids": {
            "person": max(int(manager_person.id), int(allowed_person.id), int(blocked_person.id)),
            "cost_center": blocked_cost_center.id,
            "undertaking": blocked_undertaking.id,
            "company": blocked_company.id,
            "order": blocked_order.id,
            "contract": blocked_contract.id,
        },
        "allowed_ids": {
            Company: {allowed_company.id},
            Contract: {allowed_contract.id},
            Person: {allowed_person.id},
            Order: {allowed_order.id},
            OrderVersion: {allowed_order_version.id},
            Undertaking: {allowed_undertaking.id},
            CostCenter: {allowed_cost_center.id},
            Engagement: {allowed_engagement.id},
            EngagementOrderVersionAssignment: {allowed_order_assignment.id},
            EngagementUndertakingAssignment: {allowed_undertaking_assignment.id},
            Leave: {allowed_leave.id},
        },
        "manager_extra_ids": {
            Person: {manager_person.id},
        },
        "blocked_ids": {
            Company: {blocked_company.id},
            Contract: {blocked_contract.id},
            Person: {blocked_person.id},
            Order: {blocked_order.id},
            OrderVersion: {blocked_order_version.id},
            Undertaking: {blocked_undertaking.id},
            CostCenter: {blocked_cost_center.id},
            Engagement: {blocked_engagement.id},
            EngagementOrderVersionAssignment: {blocked_order_assignment.id},
            EngagementUndertakingAssignment: {blocked_undertaking_assignment.id},
            Leave: {blocked_leave.id},
        },
    }


ENTITY_CHECKERS = [
    (Company, access_company),
    (Contract, access_contract),
    (Person, access_person),
    (Order, access_order),
    (OrderVersion, access_order_version),
    (Undertaking, access_undertaking),
    (CostCenter, access_cost_center),
    (Engagement, access_engagement),
    (EngagementOrderVersionAssignment, access_engagement_order_version_assignment),
    (EngagementUndertakingAssignment, access_engagement_undertaking_assignment),
    (Leave, access_leave),
]


ROLE_CASES = [
    ("admin", Admin),
    ("undertaking_manager", UndertakingManager),
    ("person", PersonRole),
]


@pytest.mark.django_db
@pytest.mark.parametrize(("model_cls", "checker"), ENTITY_CHECKERS)
@pytest.mark.parametrize(("role_name", "role_cls"), ROLE_CASES)
def test_accessible_to_matches_object_checker(seeded_access_data, model_cls, checker, role_name, role_cls):
    user = seeded_access_data["users"][role_name]

    expected_ids = {obj.pk for obj in model_cls.objects.all() if checker(role_cls, user, obj)}
    actual_ids = set(model_cls.objects.accessible_to(user).values_list("pk", flat=True))

    assert actual_ids == expected_ids


@pytest.mark.django_db
@pytest.mark.parametrize(("model_cls", "checker"), ENTITY_CHECKERS)
def test_role_specific_accessible_to_results_are_expected(seeded_access_data, model_cls, checker):
    del checker
    admin_user = seeded_access_data["users"]["admin"]
    manager_user = seeded_access_data["users"]["undertaking_manager"]
    person_user = seeded_access_data["users"]["person"]

    assert set(model_cls.objects.accessible_to(admin_user).values_list("pk", flat=True)) == set(
        model_cls.objects.values_list("pk", flat=True)
    )
    expected_manager_ids = seeded_access_data["allowed_ids"][model_cls] | seeded_access_data["manager_extra_ids"].get(
        model_cls, set()
    )
    assert set(model_cls.objects.accessible_to(manager_user).values_list("pk", flat=True)) == expected_manager_ids
    assert seeded_access_data["blocked_ids"][model_cls].isdisjoint(
        model_cls.objects.accessible_to(manager_user).values_list("pk", flat=True)
    )
    assert (
        set(model_cls.objects.accessible_to(person_user).values_list("pk", flat=True))
        == seeded_access_data["allowed_ids"][model_cls]
    )


def _seed_noise_data(seed_ids):
    for offset in range(1, 8):
        person_id = f"{seed_ids['person'] + offset:06d}"
        noise_person = Person.objects.create(id=person_id, first_name="Noise", last_name=f"Person {offset}")
        noise_cost_center = CostCenter.objects.create(id=seed_ids["cost_center"] + offset, name=f"Noise CC {offset}")
        noise_undertaking = Undertaking.objects.create(
            id=seed_ids["undertaking"] + offset,
            name=f"Noise Undertaking {offset}",
            cost_center=noise_cost_center,
            manager=noise_person,
        )
        noise_company = Company.objects.create(
            id=seed_ids["company"] + offset,
            name=f"Noise Company {offset}",
            email=f"noise{offset}@example.com",
        )
        noise_order = Order.objects.create(
            id=seed_ids["order"] + offset,
            name=f"Noise Order {offset}",
            company=noise_company,
        )
        noise_contract = Contract.objects.create(
            id=seed_ids["contract"] + offset,
            name=f"Noise Contract {offset}",
            status="active",
            size=1,
        )
        noise_order_version = OrderVersion.objects.create(
            order=noise_order,
            contract=noise_contract,
            version_number=1,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )
        noise_engagement = Engagement.objects.create(
            person=noise_person,
            start_date=date(2025, 1, 1) + timedelta(days=offset),
            end_date=date(2025, 12, 31),
            daily_rate=100,
            fte=1,
        )
        noise_order_assignment = EngagementOrderVersionAssignment(
            engagement=noise_engagement, order_version=noise_order_version
        )
        noise_order_assignment.save()
        EngagementUndertakingAssignment.objects.create(
            engagement=noise_engagement,
            undertaking=noise_undertaking,
            start_date=noise_engagement.start_date,
            end_date=noise_engagement.end_date,
            percentage=Decimal("1.00"),
        )
        Leave.objects.create(
            person=noise_person,
            start_date=noise_engagement.start_date,
            end_date=noise_engagement.start_date,
            percentage=Decimal("0.50"),
        )


def _evaluate_query_count(model_cls, user_id):
    user = User.objects.get(pk=user_id)
    with CaptureQueriesContext(connection) as queries:
        list(model_cls.objects.accessible_to(user))
    return len(queries)


@pytest.mark.django_db
@pytest.mark.parametrize(("model_cls", "checker"), ENTITY_CHECKERS)
@pytest.mark.parametrize("role_name", ["admin", "undertaking_manager", "person"])
def test_accessible_to_query_count_is_constant(seeded_access_data, model_cls, checker, role_name):
    del checker
    user = seeded_access_data["users"][role_name]
    initial_count = _evaluate_query_count(model_cls, user.id)

    _seed_noise_data(seeded_access_data["seed_ids"])

    after_growth_count = _evaluate_query_count(model_cls, user.id)
    assert after_growth_count == initial_count
