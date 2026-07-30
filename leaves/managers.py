"""Managers for the leaves app."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from rolepermissions.checkers import has_role


def _get_user_person_pk(user: User) -> object | None:
    """Return the primary key of the person's profile linked to the user."""
    try:
        return user.person.pk
    except ObjectDoesNotExist:
        return None


class LeaveQuerySet(models.QuerySet):  # type: ignore[type-arg]  # TODO(P8): add [Leave] once strict scope widens
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
