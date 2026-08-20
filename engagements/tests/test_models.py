"""Model invariant tests for the ``engagements`` app.

Covers FR-12 (Engagement.fte range), FR-13 (single-order constraint on
EngagementOrderVersionAssignment), FR-14 (within-span, no overlap on
EngagementUndertakingAssignment), and FR-15 (assignment dates auto-adjust
when the parent Engagement is saved).
"""

from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from engagements.models import EngagementUndertakingAssignment
from engagements.services import update_engagement
from engagements.tests.factories import (
    EngagementFactory,
    EngagementOrderVersionAssignmentFactory,
    EngagementUndertakingAssignmentFactory,
)
from orders.tests.factories import OrderFactory, OrderVersionFactory
from undertakings.tests.factories import UndertakingFactory

# ─── FR-12: Engagement.fte in [0, 1] ─────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize("valid_fte", [Decimal("0.01"), Decimal("0.50"), Decimal("1.00")])
def test_engagement_fte_accepts_values_in_range(valid_fte: Decimal) -> None:
    """FR-12: FTE strictly greater than 0 and up to 1 is accepted."""
    engagement = EngagementFactory(fte=valid_fte)
    assert engagement.fte == valid_fte


@pytest.mark.django_db
@pytest.mark.parametrize("invalid_fte", [Decimal("0.00"), Decimal("-0.10"), Decimal("1.01")])
def test_engagement_fte_rejects_out_of_range(invalid_fte: Decimal) -> None:
    """FR-12: FTE ≤ 0 or > 1 raises ValidationError."""
    with pytest.raises(ValidationError):
        EngagementFactory(fte=invalid_fte)


# ─── FR-13: single-order constraint on EngagementOrderVersionAssignment ──────


@pytest.mark.django_db
def test_order_version_assignment_accepts_matching_order() -> None:
    """FR-13: assignment is created when engagement and order_version share an order."""
    order = OrderFactory()
    version = OrderVersionFactory(order=order)
    engagement = EngagementFactory()
    EngagementOrderVersionAssignmentFactory(engagement=engagement, order_version=version)

    other_version = OrderVersionFactory(
        order=order,
        version_number=2,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
    )
    EngagementOrderVersionAssignmentFactory(engagement=engagement, order_version=other_version)

    assert engagement.order_version_assignments.count() == 2


@pytest.mark.django_db
def test_order_version_assignment_rejects_different_order() -> None:
    """FR-13: assignment across two different orders raises ValidationError."""
    engagement = EngagementFactory()
    first_version = OrderVersionFactory()
    EngagementOrderVersionAssignmentFactory(engagement=engagement, order_version=first_version)

    other_order = OrderFactory()
    conflicting_version = OrderVersionFactory(order=other_order)

    with pytest.raises(ValidationError):
        EngagementOrderVersionAssignmentFactory(engagement=engagement, order_version=conflicting_version)


# ─── FR-14: EngagementUndertakingAssignment within-span and no-overlap ───────


@pytest.mark.django_db
def test_undertaking_assignment_accepts_within_engagement_span() -> None:
    """FR-14: assignment dates fully inside the engagement span are accepted."""
    engagement = EngagementFactory(start_date=date(2024, 1, 1), end_date=date(2024, 6, 30))
    assignment = EngagementUndertakingAssignmentFactory(
        engagement=engagement,
        start_date=date(2024, 2, 1),
        end_date=date(2024, 3, 31),
    )
    assert assignment.pk is not None


@pytest.mark.django_db
def test_undertaking_assignment_rejects_start_before_engagement() -> None:
    """FR-14: assignment starting before the engagement raises ValidationError."""
    engagement = EngagementFactory(start_date=date(2024, 3, 1), end_date=date(2024, 6, 30))
    with pytest.raises(ValidationError):
        EngagementUndertakingAssignmentFactory(
            engagement=engagement,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
        )


@pytest.mark.django_db
def test_undertaking_assignment_rejects_end_after_engagement() -> None:
    """FR-14: assignment ending after the engagement raises ValidationError."""
    engagement = EngagementFactory(start_date=date(2024, 1, 1), end_date=date(2024, 3, 31))
    with pytest.raises(ValidationError):
        EngagementUndertakingAssignmentFactory(
            engagement=engagement,
            start_date=date(2024, 3, 1),
            end_date=date(2024, 6, 30),
        )


@pytest.mark.django_db
def test_undertaking_assignment_rejects_overlap_same_pair() -> None:
    """FR-14: overlapping assignments for the same (engagement, undertaking) are rejected."""
    engagement = EngagementFactory(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))
    undertaking = UndertakingFactory()
    EngagementUndertakingAssignmentFactory(
        engagement=engagement,
        undertaking=undertaking,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 6, 30),
    )
    with pytest.raises(ValidationError):
        EngagementUndertakingAssignmentFactory(
            engagement=engagement,
            undertaking=undertaking,
            start_date=date(2024, 6, 1),
            end_date=date(2024, 9, 30),
        )


@pytest.mark.django_db
def test_undertaking_assignment_allows_adjacent_same_pair() -> None:
    """FR-14: adjacent (non-overlapping) assignments for the same pair are accepted."""
    engagement = EngagementFactory(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))
    undertaking = UndertakingFactory()
    EngagementUndertakingAssignmentFactory(
        engagement=engagement,
        undertaking=undertaking,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 6, 30),
    )
    second = EngagementUndertakingAssignmentFactory(
        engagement=engagement,
        undertaking=undertaking,
        start_date=date(2024, 7, 1),
        end_date=date(2024, 12, 31),
    )
    assert second.pk is not None


# ─── FR-15: update_engagement service adjusts child assignment dates ─────────
#
# FR-15 is enforced by ``engagements.services.update_engagement`` (P2.T3), not
# by ``Engagement.save`` — the model save keeps invariants local to itself.


@pytest.mark.django_db
def test_update_engagement_shrinks_assignment_to_new_end_date() -> None:
    """FR-15: shortening an engagement clips assignments extending past its end."""
    engagement = EngagementFactory(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))
    undertaking = UndertakingFactory()
    assignment = EngagementUndertakingAssignmentFactory(
        engagement=engagement,
        undertaking=undertaking,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
    )

    engagement.end_date = date(2024, 6, 30)
    update_engagement(engagement=engagement)

    assignment.refresh_from_db()
    assert assignment.end_date == date(2024, 6, 30)


@pytest.mark.django_db
def test_update_engagement_shifts_assignment_to_new_start_date() -> None:
    """FR-15: pushing an engagement's start forward clips assignments starting earlier."""
    engagement = EngagementFactory(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))
    undertaking = UndertakingFactory()
    assignment = EngagementUndertakingAssignmentFactory(
        engagement=engagement,
        undertaking=undertaking,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
    )

    engagement.start_date = date(2024, 3, 1)
    update_engagement(engagement=engagement)

    assignment.refresh_from_db()
    assert assignment.start_date == date(2024, 3, 1)


@pytest.mark.django_db
def test_update_engagement_leaves_in_span_assignments_unchanged() -> None:
    """FR-15: assignments already fully inside the engagement span are left alone."""
    engagement = EngagementFactory(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))
    undertaking = UndertakingFactory()
    assignment = EngagementUndertakingAssignmentFactory(
        engagement=engagement,
        undertaking=undertaking,
        start_date=date(2024, 4, 1),
        end_date=date(2024, 5, 31),
    )

    engagement.end_date = date(2024, 10, 31)
    update_engagement(engagement=engagement)

    assignment.refresh_from_db()
    assert assignment.start_date == date(2024, 4, 1)
    assert assignment.end_date == date(2024, 5, 31)


@pytest.mark.django_db
def test_engagement_end_before_start_rejected() -> None:
    """Engagement.clean rejects end_date < start_date."""
    with pytest.raises(ValidationError):
        EngagementFactory(start_date=date(2024, 6, 1), end_date=date(2024, 1, 1))


# ─── Sanity check on the assignment cascade path ─────────────────────────────


@pytest.mark.django_db
def test_assignment_query_after_engagement_shrink_uses_new_bounds() -> None:
    """FR-15: querying assignments after update_engagement returns the clipped end_date."""
    engagement = EngagementFactory(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))
    undertaking = UndertakingFactory()
    EngagementUndertakingAssignmentFactory(
        engagement=engagement,
        undertaking=undertaking,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
    )

    engagement.end_date = date(2024, 3, 31)
    update_engagement(engagement=engagement)

    assignment = EngagementUndertakingAssignment.objects.get(engagement=engagement, undertaking=undertaking)
    assert assignment.end_date == date(2024, 3, 31)
