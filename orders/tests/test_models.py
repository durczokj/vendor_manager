"""Model invariant tests for the ``orders`` app.

Covers FR-16: on every OrderVersion create/update the model enforces
``start_date <= end_date``, gap-free version numbers within an Order,
and non-overlapping date ranges within an Order.
"""

from datetime import date

import pytest
from django.core.exceptions import ValidationError

from orders.tests.factories import OrderFactory, OrderVersionFactory

# ─── FR-16: start_date <= end_date ───────────────────────────────────────────


@pytest.mark.django_db
def test_order_version_accepts_start_before_end() -> None:
    """FR-16: start_date < end_date is accepted."""
    order = OrderFactory()
    version = OrderVersionFactory(
        order=order,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
    )
    assert version.pk is not None


@pytest.mark.django_db
def test_order_version_accepts_start_equal_to_end() -> None:
    """FR-16: start_date == end_date is accepted (single-day version)."""
    order = OrderFactory()
    version = OrderVersionFactory(
        order=order,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 1),
    )
    assert version.pk is not None


@pytest.mark.django_db
def test_order_version_rejects_end_before_start() -> None:
    """FR-16: end_date < start_date raises ValidationError."""
    order = OrderFactory()
    with pytest.raises(ValidationError):
        OrderVersionFactory(
            order=order,
            start_date=date(2024, 6, 1),
            end_date=date(2024, 1, 1),
        )


# ─── FR-16: gap-free version numbers within an Order ─────────────────────────


@pytest.mark.django_db
def test_order_version_accepts_gap_free_chain() -> None:
    """FR-16: the next version starts on ``previous.end_date + 1 day``."""
    order = OrderFactory()
    OrderVersionFactory(
        order=order,
        version_number=1,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 6, 30),
    )
    v2 = OrderVersionFactory(
        order=order,
        version_number=2,
        start_date=date(2024, 7, 1),
        end_date=date(2024, 12, 31),
    )
    assert v2.pk is not None


@pytest.mark.django_db
def test_order_version_rejects_gap_between_versions() -> None:
    """FR-16: leaving a gap between versions raises ValidationError."""
    order = OrderFactory()
    OrderVersionFactory(
        order=order,
        version_number=1,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 6, 30),
    )
    with pytest.raises(ValidationError):
        OrderVersionFactory(
            order=order,
            version_number=2,
            start_date=date(2024, 8, 1),
            end_date=date(2024, 12, 31),
        )


# ─── FR-16: non-overlapping date ranges within an Order ──────────────────────


@pytest.mark.django_db
def test_order_version_rejects_overlapping_range_within_order() -> None:
    """FR-16: a new version overlapping an existing one is rejected."""
    order = OrderFactory()
    OrderVersionFactory(
        order=order,
        version_number=1,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 6, 30),
    )
    with pytest.raises(ValidationError):
        OrderVersionFactory(
            order=order,
            version_number=2,
            start_date=date(2024, 5, 1),
            end_date=date(2024, 9, 30),
        )


@pytest.mark.django_db
def test_order_version_allows_same_dates_on_different_orders() -> None:
    """FR-16: gap-free / no-overlap rules are scoped to a single order."""
    order_a = OrderFactory()
    v1 = OrderVersionFactory(
        order=order_a,
        version_number=1,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 6, 30),
    )
    order_b = OrderFactory()
    v2 = OrderVersionFactory(
        order=order_b,
        version_number=1,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 6, 30),
    )
    assert v1.pk != v2.pk
