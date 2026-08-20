"""Factory-boy factories for the ``contracts`` app."""

from __future__ import annotations

import factory

from contracts.models import Contract


class ContractFactory(factory.django.DjangoModelFactory):
    """Build a ``Contract`` with a unique id and neutral defaults."""

    class Meta:
        model = Contract

    id = factory.Sequence(lambda n: 20_000 + n)
    name = factory.Sequence(lambda n: f"Contract {n}")
    status = "active"
    size = 1
