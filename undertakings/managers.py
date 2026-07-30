"""Managers for the undertakings app."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models


class CostCenterQuerySet(models.QuerySet):  # type: ignore[type-arg]  # TODO(P8): add [CostCenter] once strict scope widens
    """QuerySet for the CostCenter model."""

    def accessible_to(self, user: User) -> CostCenterQuerySet:
        """Return cost centers accessible to the given user.

        Args:
            user: The authenticated user.

        Returns:
            A filtered CostCenterQuerySet.

        Raises:
            NotImplementedError: Implementation lands in P2.T5.
        """
        raise NotImplementedError


CostCenterManager = models.Manager.from_queryset(CostCenterQuerySet)


class UndertakingQuerySet(models.QuerySet):  # type: ignore[type-arg]  # TODO(P8): add [Undertaking] once strict scope widens
    """QuerySet for the Undertaking model."""

    def accessible_to(self, user: User) -> UndertakingQuerySet:
        """Return undertakings accessible to the given user.

        Args:
            user: The authenticated user.

        Returns:
            A filtered UndertakingQuerySet.

        Raises:
            NotImplementedError: Implementation lands in P2.T5.
        """
        raise NotImplementedError


UndertakingManager = models.Manager.from_queryset(UndertakingQuerySet)
