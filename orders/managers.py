"""Managers for the orders app."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models


class OrderQuerySet(models.QuerySet):  # type: ignore[type-arg]  # TODO(P8): add [Order] once strict scope widens
    """QuerySet for the Order model."""

    def accessible_to(self, user: User) -> OrderQuerySet:
        """Return orders accessible to the given user.

        Args:
            user: The authenticated user.

        Returns:
            A filtered OrderQuerySet.

        Raises:
            NotImplementedError: Implementation lands in P2.T5.
        """
        raise NotImplementedError


OrderManager = models.Manager.from_queryset(OrderQuerySet)


class OrderVersionQuerySet(models.QuerySet):  # type: ignore[type-arg]  # TODO(P8): add [OrderVersion] once strict scope widens
    """QuerySet for the OrderVersion model."""

    def accessible_to(self, user: User) -> OrderVersionQuerySet:
        """Return order versions accessible to the given user.

        Args:
            user: The authenticated user.

        Returns:
            A filtered OrderVersionQuerySet.

        Raises:
            NotImplementedError: Implementation lands in P2.T5.
        """
        raise NotImplementedError


OrderVersionManager = models.Manager.from_queryset(OrderVersionQuerySet)
