"""Service layer for orders."""

from datetime import date, timedelta

from django.db import transaction

from contracts.models import Contract
from orders.models import Order, OrderVersion


def create_new_order_version(
    *,
    order: Order,
    contract: Contract,
    start_date: date,
    end_date: date,
    copy_engagement_assignments: bool = True,
) -> OrderVersion:
    """Create a new order version and optionally copy engagement assignments."""
    with transaction.atomic():
        last_version = order.versions.order_by("-version_number").first()
        assert last_version is not None, "cannot create a new version without an existing one"

        last_version.end_date = start_date - timedelta(days=1)
        last_version.clean()
        last_version.save()

        contract.save()

        new_version = OrderVersion(
            order=order,
            contract=contract,
            version_number=last_version.version_number + 1,
            start_date=start_date,
            end_date=end_date,
        )

        new_version.clean()
        new_version.save()

        if copy_engagement_assignments:
            for assignment in last_version.engagement_assignments.all():
                assignment.pk = None
                assignment.order_version = new_version
                assignment.save()

    return new_version
