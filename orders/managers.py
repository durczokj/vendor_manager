"""Managers for the orders app."""

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


class OrderQuerySet(models.QuerySet):  # type: ignore[type-arg]  # TODO(P8): add [Order] once strict scope widens
    """QuerySet for the Order model."""

    def accessible_to(self, user: User) -> OrderQuerySet:
        """Return orders accessible to the given user.

        Args:
            user: The authenticated user.

        Returns:
            A filtered OrderQuerySet.

        """
        if has_role(user, "admin"):
            return self

        person_pk = _get_user_person_pk(user)
        if person_pk is None:
            return self.none()

        if has_role(user, "undertaking_manager"):
            return self.filter(
                versions__engagement_assignments__engagement__undertaking_assignments__undertaking__manager_id=person_pk
            ).distinct()

        if has_role(user, "person"):
            return self.filter(versions__engagement_assignments__engagement__person_id=person_pk).distinct()

        return self.none()


OrderManager = models.Manager.from_queryset(OrderQuerySet)


class OrderVersionQuerySet(models.QuerySet):  # type: ignore[type-arg]  # TODO(P8): add [OrderVersion] once strict scope widens
    """QuerySet for the OrderVersion model."""

    def accessible_to(self, user: User) -> OrderVersionQuerySet:
        """Return order versions accessible to the given user.

        Args:
            user: The authenticated user.

        Returns:
            A filtered OrderVersionQuerySet.

        """
        if has_role(user, "admin"):
            return self

        person_pk = _get_user_person_pk(user)
        if person_pk is None:
            return self.none()

        if has_role(user, "undertaking_manager"):
            return self.filter(
                engagement_assignments__engagement__undertaking_assignments__undertaking__manager_id=person_pk
            ).distinct()

        if has_role(user, "person"):
            return self.filter(engagement_assignments__engagement__person_id=person_pk).distinct()

        return self.none()


OrderVersionManager = models.Manager.from_queryset(OrderVersionQuerySet)
