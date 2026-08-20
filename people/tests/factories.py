"""Factory-boy factories for the ``people`` app."""

from __future__ import annotations

import factory
from django.contrib.auth.models import User

from people.models import Person


class UserFactory(factory.django.DjangoModelFactory):
    """Build a ``User`` with a unique username."""

    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: f"user-{n}")


class PersonFactory(factory.django.DjangoModelFactory):
    """Build a ``Person`` with a 6-character id and blank optional fields."""

    class Meta:
        model = Person

    id = factory.Sequence(lambda n: f"P{n:05d}")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    description = ""
    location = ""
    user = None
