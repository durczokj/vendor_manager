"""Managers for the orders app."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from rolepermissions.checkers import has_role

if TYPE_CHECKING:
    from orders.models import Order, OrderVersion

    _OrderQuerySetBase = models.QuerySet[Order]
    _OrderVersionQuerySetBase = models.QuerySet[OrderVersion]
else:
    _OrderQuerySetBase = models.QuerySet
    _OrderVersionQuerySetBase = models.QuerySet


def _get_user_person_pk(user: User) -> str | None:
    """Return the primary key of the person's profile linked to the user."""
    try:
        return str(user.person.pk)
    except ObjectDoesNotExist:
        return None


class OrderQuerySet(_OrderQuerySetBase):
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


class OrderVersionQuerySet(_OrderVersionQuerySetBase):
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
