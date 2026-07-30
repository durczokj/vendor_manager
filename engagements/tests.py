from datetime import date

import pytest

from engagements.forms import EngagementForm
from engagements.models import Engagement, EngagementUndertakingAssignment
from engagements.services import update_engagement
from people.models import Person
from undertakings.models import CostCenter, Undertaking


def _create_assignment_fixture() -> tuple[Engagement, EngagementUndertakingAssignment]:
    manager = Person.objects.create(id="000001", first_name="Casey", last_name="Manager")
    person = Person.objects.create(id="000002", first_name="Pat", last_name="Consultant")
    cost_center = CostCenter.objects.create(id=1, name="CC1")
    undertaking = Undertaking.objects.create(id=1, name="U1", cost_center=cost_center, manager=manager)
    engagement = Engagement.objects.create(
        person=person,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        daily_rate=100,
        fte=1,
    )
    assignment = EngagementUndertakingAssignment.objects.create(
        engagement=engagement,
        undertaking=undertaking,
        start_date=date(2024, 2, 1),
        end_date=date(2024, 11, 30),
        percentage=1,
    )
    return engagement, assignment


@pytest.mark.django_db
def test_update_engagement_adjusts_existing_assignment_dates():
    engagement, assignment = _create_assignment_fixture()

    engagement.start_date = date(2024, 3, 1)
    engagement.end_date = date(2024, 10, 31)
    update_engagement(engagement=engagement)

    assignment.refresh_from_db()
    assert assignment.start_date == date(2024, 3, 1)
    assert assignment.end_date == date(2024, 10, 31)


@pytest.mark.django_db
def test_engagement_form_update_applies_service_date_adjustment():
    engagement, assignment = _create_assignment_fixture()

    form = EngagementForm(
        data={
            "person": engagement.person_id,
            "start_date": "2024-03-01",
            "end_date": "2024-10-31",
            "daily_rate": "100.00",
            "fte": "1.00",
        },
        instance=engagement,
    )

    assert form.is_valid()
    form.save()

    assignment.refresh_from_db()
    assert assignment.start_date == date(2024, 3, 1)
    assert assignment.end_date == date(2024, 10, 31)
