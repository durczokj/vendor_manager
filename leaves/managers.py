"""Managers for the leaves app."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from rolepermissions.checkers import has_role

if TYPE_CHECKING:
    from leaves.models import Leave

    _LeaveQuerySetBase = models.QuerySet[Leave]
else:
    _LeaveQuerySetBase = models.QuerySet


def _get_user_person_pk(user: User) -> str | None:
    """Return the primary key of the person's profile linked to the user."""
    try:
        return str(user.person.pk)
    except ObjectDoesNotExist:
        return None


class LeaveQuerySet(_LeaveQuerySetBase):
    """QuerySet for the Leave model."""

    def accessible_to(self, user: User) -> LeaveQuerySet:
        """Return leaves accessible to the given user.

        Args:
            user: The authenticated user.

        Returns:
            A filtered LeaveQuerySet.

        """
        if has_role(user, "admin"):
            return self

        person_pk = _get_user_person_pk(user)
        if person_pk is None:
            return self.none()

        if has_role(user, "undertaking_manager"):
            return self.filter(
                person__engagements__undertaking_assignments__undertaking__manager_id=person_pk
            ).distinct()

        if has_role(user, "person"):
            return self.filter(person_id=person_pk)

        return self.none()


LeaveManager = models.Manager.from_queryset(LeaveQuerySet)
