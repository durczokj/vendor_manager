"""Managers for the engagements app."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models


class EngagementQuerySet(models.QuerySet):  # type: ignore[type-arg]  # TODO(P8): add [Engagement] once strict scope widens
    """QuerySet for the Engagement model."""

    def accessible_to(self, user: User) -> EngagementQuerySet:
        """Return engagements accessible to the given user.

        Args:
            user: The authenticated user.

        Returns:
            A filtered EngagementQuerySet.

        Raises:
            NotImplementedError: Implementation lands in P2.T5.
        """
        raise NotImplementedError


EngagementManager = models.Manager.from_queryset(EngagementQuerySet)


class EngagementOrderVersionAssignmentQuerySet(models.QuerySet):  # type: ignore[type-arg]  # TODO(P8): add [EngagementOrderVersionAssignment]
    """QuerySet for the EngagementOrderVersionAssignment model."""

    def accessible_to(self, user: User) -> EngagementOrderVersionAssignmentQuerySet:
        """Return engagement–order-version assignments accessible to the given user.

        Args:
            user: The authenticated user.

        Returns:
            A filtered EngagementOrderVersionAssignmentQuerySet.

        Raises:
            NotImplementedError: Implementation lands in P2.T5.
        """
        raise NotImplementedError


EngagementOrderVersionAssignmentManager = models.Manager.from_queryset(EngagementOrderVersionAssignmentQuerySet)


class EngagementUndertakingAssignmentQuerySet(models.QuerySet):  # type: ignore[type-arg]  # TODO(P8): add [EngagementUndertakingAssignment]
    """QuerySet for the EngagementUndertakingAssignment model."""

    def accessible_to(self, user: User) -> EngagementUndertakingAssignmentQuerySet:
        """Return engagement–undertaking assignments accessible to the given user.

        Args:
            user: The authenticated user.

        Returns:
            A filtered EngagementUndertakingAssignmentQuerySet.

        Raises:
            NotImplementedError: Implementation lands in P2.T5.
        """
        raise NotImplementedError


EngagementUndertakingAssignmentManager = models.Manager.from_queryset(EngagementUndertakingAssignmentQuerySet)
