"""Managers for the leaves app."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models


class LeaveQuerySet(models.QuerySet):  # type: ignore[type-arg]  # TODO(P8): add [Leave] once strict scope widens
    """QuerySet for the Leave model."""

    def accessible_to(self, user: User) -> LeaveQuerySet:
        """Return leaves accessible to the given user.

        Args:
            user: The authenticated user.

        Returns:
            A filtered LeaveQuerySet.

        Raises:
            NotImplementedError: Implementation lands in P2.T5.
        """
        raise NotImplementedError


LeaveManager = models.Manager.from_queryset(LeaveQuerySet)
