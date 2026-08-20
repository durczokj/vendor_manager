"""Tests for engagement form and update-service date adjustment.

Migrated from the old top-level ``engagements/tests.py`` module during P7.T1
so the tests package can coexist with ``engagements/tests/factories.py``.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from engagements.forms import EngagementForm
from engagements.models import Engagement, EngagementUndertakingAssignment
from engagements.services import update_engagement
from engagements.tests.factories import EngagementFactory, EngagementUndertakingAssignmentFactory


def _create_assignment_fixture() -> tuple[Engagement, EngagementUndertakingAssignment]:
    engagement = EngagementFactory(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        daily_rate=Decimal("100.00"),
        fte=Decimal("1.00"),
    )
    assignment = EngagementUndertakingAssignmentFactory(
        engagement=engagement,
        start_date=date(2024, 2, 1),
        end_date=date(2024, 11, 30),
        percentage=Decimal("1.00"),
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
