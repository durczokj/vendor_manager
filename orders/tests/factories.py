"""Factory-boy factories for the ``orders`` app."""

from __future__ import annotations

from datetime import date

import factory

from companies.tests.factories import CompanyFactory
from contracts.tests.factories import ContractFactory
from orders.models import Order, OrderVersion


class OrderFactory(factory.django.DjangoModelFactory):
    """Build an ``Order`` attached to a fresh company."""

    class Meta:
        model = Order

    id = factory.Sequence(lambda n: 50_000 + n)
    name = factory.Sequence(lambda n: f"Order {n}")
    company = factory.SubFactory(CompanyFactory)


class OrderVersionFactory(factory.django.DjangoModelFactory):
    """Build an ``OrderVersion`` starting on 2024-01-01.

    ``version_number`` is unique per order, and the previous version's ``end_date``
    must be exactly ``start_date - 1`` day. Callers building a chain MUST override
    ``version_number`` and dates explicitly to keep FR-16 invariants intact.
    """

    class Meta:
        model = OrderVersion

    order = factory.SubFactory(OrderFactory)
    contract = factory.SubFactory(ContractFactory)
    version_number = 1
    start_date = date(2024, 1, 1)
    end_date = date(2024, 12, 31)
