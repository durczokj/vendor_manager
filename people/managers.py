"""Managers for the people app."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from rolepermissions.checkers import has_role

if TYPE_CHECKING:
    from people.models import Person

    _PersonQuerySetBase = models.QuerySet[Person]
else:
    _PersonQuerySetBase = models.QuerySet


def _get_user_person_pk(user: User) -> str | None:
    """Return the primary key of the person's profile linked to the user."""
    try:
        return str(user.person.pk)
    except ObjectDoesNotExist:
        return None


class PersonQuerySet(_PersonQuerySetBase):
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
