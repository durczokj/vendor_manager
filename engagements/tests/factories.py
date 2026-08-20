"""Factory-boy factories for the ``engagements`` app."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import factory

from engagements.models import (
    Engagement,
    EngagementOrderVersionAssignment,
    EngagementUndertakingAssignment,
)
from orders.tests.factories import OrderVersionFactory
from people.tests.factories import PersonFactory
from undertakings.tests.factories import UndertakingFactory


class EngagementFactory(factory.django.DjangoModelFactory):
    """Build an ``Engagement`` covering the 2024 calendar year at 1.0 FTE."""

    class Meta:
        model = Engagement

    person = factory.SubFactory(PersonFactory)
    start_date = date(2024, 1, 1)
    end_date = date(2024, 12, 31)
    daily_rate = Decimal("100.00")
    fte = Decimal("1.00")


class EngagementOrderVersionAssignmentFactory(factory.django.DjangoModelFactory):
    """Attach an engagement to an order version."""

    class Meta:
        model = EngagementOrderVersionAssignment

    engagement = factory.SubFactory(EngagementFactory)
    order_version = factory.SubFactory(OrderVersionFactory)


class EngagementUndertakingAssignmentFactory(factory.django.DjangoModelFactory):
    """Attach an engagement to an undertaking.

    Defaults align dates to the engagement's own span so the FR-14 within-span
    check passes.
    """

    class Meta:
        model = EngagementUndertakingAssignment

    engagement = factory.SubFactory(EngagementFactory)
    undertaking = factory.SubFactory(UndertakingFactory)
    start_date = factory.SelfAttribute("engagement.start_date")
    end_date = factory.SelfAttribute("engagement.end_date")
    percentage = Decimal("1.00")
