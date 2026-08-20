"""Factory-boy factories for the ``leaves`` app."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import factory

from leaves.models import Leave
from people.tests.factories import PersonFactory


class LeaveFactory(factory.django.DjangoModelFactory):
    """Build a ``Leave`` for a fresh person in early 2024."""

    class Meta:
        model = Leave

    person = factory.SubFactory(PersonFactory)
    start_date = date(2024, 1, 1)
    end_date = date(2024, 1, 2)
    percentage = Decimal("1.00")
