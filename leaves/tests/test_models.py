"""Model invariant tests for the ``leaves`` app.

Covers FR-17: ``Leave.percentage`` MUST be in [0, 1]. Also asserts the
supporting date-range invariant enforced by ``Leave.clean``.
"""

from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from leaves.tests.factories import LeaveFactory

# ─── FR-17: Leave.percentage in [0, 1] ───────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize("valid_percentage", [Decimal("0.00"), Decimal("0.25"), Decimal("1.00")])
def test_leave_percentage_accepts_values_in_range(valid_percentage: Decimal) -> None:
    """FR-17: percentages inside [0, 1] are accepted."""
    leave = LeaveFactory(percentage=valid_percentage)
    assert leave.percentage == valid_percentage


@pytest.mark.django_db
@pytest.mark.parametrize("invalid_percentage", [Decimal("-0.01"), Decimal("1.01"), Decimal("2.00")])
def test_leave_percentage_rejects_out_of_range(invalid_percentage: Decimal) -> None:
    """FR-17: percentages outside [0, 1] raise ValidationError."""
    with pytest.raises(ValidationError):
        LeaveFactory(percentage=invalid_percentage).full_clean()


# ─── Supporting date invariant ───────────────────────────────────────────────


@pytest.mark.django_db
def test_leave_rejects_end_before_start() -> None:
    """Leave.clean rejects end_date < start_date."""
    with pytest.raises(ValidationError):
        LeaveFactory(start_date=date(2024, 6, 1), end_date=date(2024, 1, 1))


@pytest.mark.django_db
def test_leave_accepts_same_day_start_and_end() -> None:
    """A single-day leave (start_date == end_date) is accepted."""
    leave = LeaveFactory(start_date=date(2024, 3, 15), end_date=date(2024, 3, 15))
    assert leave.pk is not None
