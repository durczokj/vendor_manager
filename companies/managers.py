"""Managers for the companies app."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models


class CompanyQuerySet(models.QuerySet):  # type: ignore[type-arg]  # TODO(P8): add [Company] once strict scope widens
    """QuerySet for the Company model."""

    def accessible_to(self, user: User) -> CompanyQuerySet:
        """Return companies accessible to the given user.

        Args:
            user: The authenticated user.

        Returns:
            A filtered CompanyQuerySet.

        Raises:
            NotImplementedError: Implementation lands in P2.T5.
        """
        raise NotImplementedError


CompanyManager = models.Manager.from_queryset(CompanyQuerySet)
