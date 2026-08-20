"""Factory-boy factories for the ``companies`` app."""

from __future__ import annotations

import factory

from companies.models import Company


class CompanyFactory(factory.django.DjangoModelFactory):
    """Build a ``Company`` with a unique integer id and coherent email."""

    class Meta:
        model = Company

    id = factory.Sequence(lambda n: 10_000 + n)
    name = factory.Sequence(lambda n: f"Company {n}")
    email = factory.LazyAttribute(lambda o: f"contact+{o.id}@example.com")
