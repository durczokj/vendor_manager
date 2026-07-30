"""Managers for the people app."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models


class PersonQuerySet(models.QuerySet):  # type: ignore[type-arg]  # TODO(P8): add [Person] once strict scope widens
    """QuerySet for the Person model."""

    def accessible_to(self, user: User) -> PersonQuerySet:
        """Return people accessible to the given user.

        Args:
            user: The authenticated user.

        Returns:
            A filtered PersonQuerySet.

        Raises:
            NotImplementedError: Implementation lands in P2.T5.
        """
        raise NotImplementedError


PersonManager = models.Manager.from_queryset(PersonQuerySet)
