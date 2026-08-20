"""Factory-boy factories for the ``undertakings`` app."""

from __future__ import annotations

import factory

from people.tests.factories import PersonFactory
from undertakings.models import CostCenter, Undertaking


class CostCenterFactory(factory.django.DjangoModelFactory):
    """Build a ``CostCenter`` with a unique integer id."""

    class Meta:
        model = CostCenter

    id = factory.Sequence(lambda n: 30_000 + n)
    name = factory.Sequence(lambda n: f"Cost Center {n}")


class UndertakingFactory(factory.django.DjangoModelFactory):
    """Build an ``Undertaking`` with a fresh cost center and manager."""

    class Meta:
        model = Undertaking

    id = factory.Sequence(lambda n: 40_000 + n)
    name = factory.Sequence(lambda n: f"Undertaking {n}")
    cost_center = factory.SubFactory(CostCenterFactory)
    manager = factory.SubFactory(PersonFactory)
