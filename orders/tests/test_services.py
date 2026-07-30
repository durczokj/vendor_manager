from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from companies.models import Company
from contracts.models import Contract
from engagements.models import Engagement, EngagementOrderVersionAssignment
from orders.models import Order, OrderVersion
from orders.services import create_new_order_version
from people.models import Person


def create_order_with_version(
    *,
    company_id: int,
    order_id: int,
    contract_id: int,
    end_date: date,
) -> tuple[Order, OrderVersion]:
    company = Company.objects.create(
        id=company_id, name=f"Company {company_id}", email=f"company{company_id}@example.com"
    )
    order = Order.objects.create(id=order_id, name=f"Order {order_id}", company=company)
    contract = Contract.objects.create(id=contract_id, name=f"Contract {contract_id}", status="active", size=1)
    version = OrderVersion.objects.create(
        order=order,
        contract=contract,
        version_number=1,
        start_date=date(2024, 1, 1),
        end_date=end_date,
    )
    return order, version


@pytest.mark.django_db
def test_create_new_order_version_happy_path():
    order, previous_version = create_order_with_version(
        company_id=1, order_id=1, contract_id=1, end_date=date(2026, 12, 31)
    )
    contract = Contract.objects.create(id=2, name="Contract 2", status="active", size=1)
    person = Person.objects.create(id="000001", first_name="Jane", last_name="Doe")
    engagement = Engagement.objects.create(
        person=person,
        start_date=date(2024, 1, 1),
        end_date=date(2025, 12, 31),
        daily_rate=100,
        fte=1,
    )
    EngagementOrderVersionAssignment(engagement=engagement, order_version=previous_version).save()

    new_version = create_new_order_version(
        order=order,
        contract=contract,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
    )

    previous_version.refresh_from_db()
    assert previous_version.end_date == date(2024, 12, 31)
    assert new_version.version_number == 2
    assert new_version.start_date == date(2025, 1, 1)
    assert new_version.end_date == date(2025, 12, 31)
    assert new_version.engagement_assignments.count() == 1


@pytest.mark.django_db
def test_create_new_order_version_with_used_contract_raises_integrity_error():
    order, _ = create_order_with_version(company_id=1, order_id=1, contract_id=1, end_date=date(2026, 12, 31))
    second_order, _ = create_order_with_version(company_id=2, order_id=2, contract_id=2, end_date=date(2026, 12, 31))
    used_contract = second_order.versions.get(version_number=1).contract

    with pytest.raises(IntegrityError):
        create_new_order_version(
            order=order,
            contract=used_contract,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )


@pytest.mark.django_db
def test_create_new_order_version_with_start_date_not_after_previous_start_raises_validation_error():
    order, _ = create_order_with_version(company_id=1, order_id=1, contract_id=1, end_date=date(2026, 12, 31))
    contract = Contract.objects.create(id=2, name="Contract 2", status="active", size=1)

    with pytest.raises(ValidationError):
        create_new_order_version(
            order=order,
            contract=contract,
            start_date=date(2024, 1, 1),
            end_date=date(2025, 12, 31),
        )


@pytest.mark.django_db
def test_create_new_order_version_rolls_back_when_assignment_copy_fails(monkeypatch):
    order, previous_version = create_order_with_version(
        company_id=1, order_id=1, contract_id=1, end_date=date(2026, 12, 31)
    )
    contract = Contract.objects.create(id=2, name="Contract 2", status="active", size=1)
    person = Person.objects.create(id="000001", first_name="Jane", last_name="Doe")
    engagement = Engagement.objects.create(
        person=person,
        start_date=date(2024, 1, 1),
        end_date=date(2025, 12, 31),
        daily_rate=100,
        fte=1,
    )
    assignment = EngagementOrderVersionAssignment(engagement=engagement, order_version=previous_version)
    assignment.save()
    original_save = EngagementOrderVersionAssignment.save

    def fail_on_copy(self, *args, **kwargs):
        if self.pk is None:
            raise RuntimeError("copy failed")
        return original_save(self, *args, **kwargs)

    monkeypatch.setattr(EngagementOrderVersionAssignment, "save", fail_on_copy)

    with pytest.raises(RuntimeError, match="copy failed"):
        create_new_order_version(
            order=order,
            contract=contract,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )

    previous_version.refresh_from_db()
    assignment.refresh_from_db()
    assert previous_version.end_date == date(2026, 12, 31)
    assert order.versions.count() == 1
    assert assignment.order_version_id == previous_version.id
