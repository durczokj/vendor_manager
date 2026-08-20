"""Managers for the engagements app."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from rolepermissions.checkers import has_role

if TYPE_CHECKING:
    from engagements.models import (
        Engagement,
        EngagementOrderVersionAssignment,
        EngagementUndertakingAssignment,
    )

    _EngagementQuerySetBase = models.QuerySet[Engagement]
    _EngagementOrderVersionAssignmentQuerySetBase = models.QuerySet[EngagementOrderVersionAssignment]
    _EngagementUndertakingAssignmentQuerySetBase = models.QuerySet[EngagementUndertakingAssignment]
else:
    _EngagementQuerySetBase = models.QuerySet
    _EngagementOrderVersionAssignmentQuerySetBase = models.QuerySet
    _EngagementUndertakingAssignmentQuerySetBase = models.QuerySet


def _get_user_person_pk(user: User) -> str | None:
    """Return the primary key of the person's profile linked to the user."""
    try:
        return str(user.person.pk)
    except ObjectDoesNotExist:
        return None


class EngagementQuerySet(_EngagementQuerySetBase):
    """QuerySet for the Engagement model."""

    def accessible_to(self, user: User) -> EngagementQuerySet:
        """Return engagements accessible to the given user.

        Args:
            user: The authenticated user.

        Returns:
            A filtered EngagementQuerySet.

        """
        if has_role(user, "admin"):
            return self

        person_pk = _get_user_person_pk(user)
        if person_pk is None:
            return self.none()

        if has_role(user, "undertaking_manager"):
            return self.filter(undertaking_assignments__undertaking__manager_id=person_pk).distinct()

        if has_role(user, "person"):
            return self.filter(person_id=person_pk)

        return self.none()


EngagementManager = models.Manager.from_queryset(EngagementQuerySet)


class EngagementOrderVersionAssignmentQuerySet(_EngagementOrderVersionAssignmentQuerySetBase):
    """QuerySet for the EngagementOrderVersionAssignment model."""

    def accessible_to(self, user: User) -> EngagementOrderVersionAssignmentQuerySet:
        """Return engagement–order-version assignments accessible to the given user.

        Args:
            user: The authenticated user.

        Returns:
            A filtered EngagementOrderVersionAssignmentQuerySet.

        """
        if has_role(user, "admin"):
            return self

        person_pk = _get_user_person_pk(user)
        if person_pk is None:
            return self.none()

        if has_role(user, "undertaking_manager"):
            return self.filter(engagement__undertaking_assignments__undertaking__manager_id=person_pk).distinct()

        if has_role(user, "person"):
            return self.filter(engagement__person_id=person_pk).distinct()

        return self.none()


EngagementOrderVersionAssignmentManager = models.Manager.from_queryset(EngagementOrderVersionAssignmentQuerySet)


class EngagementUndertakingAssignmentQuerySet(_EngagementUndertakingAssignmentQuerySetBase):
    """QuerySet for the EngagementUndertakingAssignment model."""

    def accessible_to(self, user: User) -> EngagementUndertakingAssignmentQuerySet:
        """Return engagement–undertaking assignments accessible to the given user.

        Args:
            user: The authenticated user.

        Returns:
            A filtered EngagementUndertakingAssignmentQuerySet.

        """
        if has_role(user, "admin"):
            return self

        person_pk = _get_user_person_pk(user)
        if person_pk is None:
            return self.none()

        if has_role(user, "undertaking_manager"):
            return self.filter(undertaking__manager_id=person_pk).distinct()

        if has_role(user, "person"):
            return self.filter(engagement__person_id=person_pk).distinct()

        return self.none()


EngagementUndertakingAssignmentManager = models.Manager.from_queryset(EngagementUndertakingAssignmentQuerySet)
