"""Managers for the undertakings app."""

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


class CostCenterQuerySet(models.QuerySet):  # type: ignore[type-arg]  # TODO(P8): add [CostCenter] once strict scope widens
    """QuerySet for the CostCenter model."""

    def accessible_to(self, user: User) -> CostCenterQuerySet:
        """Return cost centers accessible to the given user.

        Args:
            user: The authenticated user.

        Returns:
            A filtered CostCenterQuerySet.

        """
        if has_role(user, "admin"):
            return self

        person_pk = _get_user_person_pk(user)
        if person_pk is None:
            return self.none()

        if has_role(user, "undertaking_manager"):
            return self.filter(undertakings__manager_id=person_pk).distinct()

        if has_role(user, "person"):
            return self.filter(undertakings__engagement_assignments__engagement__person_id=person_pk).distinct()

        return self.none()


CostCenterManager = models.Manager.from_queryset(CostCenterQuerySet)


class UndertakingQuerySet(models.QuerySet):  # type: ignore[type-arg]  # TODO(P8): add [Undertaking] once strict scope widens
    """QuerySet for the Undertaking model."""

    def accessible_to(self, user: User) -> UndertakingQuerySet:
        """Return undertakings accessible to the given user.

        Args:
            user: The authenticated user.

        Returns:
            A filtered UndertakingQuerySet.

        """
        if has_role(user, "admin"):
            return self

        person_pk = _get_user_person_pk(user)
        if person_pk is None:
            return self.none()

        if has_role(user, "undertaking_manager"):
            return self.filter(manager_id=person_pk)

        if has_role(user, "person"):
            return self.filter(engagement_assignments__engagement__person_id=person_pk).distinct()

        return self.none()


UndertakingManager = models.Manager.from_queryset(UndertakingQuerySet)
