"""Managers for the people app."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from rolepermissions.checkers import has_role


def _get_user_person_pk(user: User) -> object | None:
    """Return the primary key of the person's profile linked to the user."""
    try:
        return user.person.pk
    except ObjectDoesNotExist:
        return None


class PersonQuerySet(models.QuerySet):  # type: ignore[type-arg]  # TODO(P8): add [Person] once strict scope widens
    """QuerySet for the Person model."""

    def accessible_to(self, user: User) -> PersonQuerySet:
        """Return people accessible to the given user.

        Args:
            user: The authenticated user.

        Returns:
            A filtered PersonQuerySet.

        """
        if has_role(user, "admin"):
            return self

        person_pk = _get_user_person_pk(user)
        if person_pk is None:
            return self.none()

        if has_role(user, "undertaking_manager"):
            return self.filter(
                Q(pk=person_pk) | Q(engagements__undertaking_assignments__undertaking__manager_id=person_pk)
            ).distinct()

        if has_role(user, "person"):
            return self.filter(user=user)

        return self.none()


PersonManager = models.Manager.from_queryset(PersonQuerySet)
