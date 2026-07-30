"""Managers for the contracts app."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models


class ContractQuerySet(models.QuerySet):  # type: ignore[type-arg]  # TODO(P8): add [Contract] once strict scope widens
    """QuerySet for the Contract model."""

    def accessible_to(self, user: User) -> ContractQuerySet:
        """Return contracts accessible to the given user.

        Args:
            user: The authenticated user.

        Returns:
            A filtered ContractQuerySet.

        Raises:
            NotImplementedError: Implementation lands in P2.T5.
        """
        raise NotImplementedError


ContractManager = models.Manager.from_queryset(ContractQuerySet)
