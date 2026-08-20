"""Managers for the companies app."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from rolepermissions.checkers import has_role

if TYPE_CHECKING:
    from companies.models import Company

    _CompanyQuerySetBase = models.QuerySet[Company]
else:
    _CompanyQuerySetBase = models.QuerySet


def _get_user_person_pk(user: User) -> str | None:
    """Return the primary key of the person's profile linked to the user."""
    try:
        return str(user.person.pk)
    except ObjectDoesNotExist:
        return None


class CompanyQuerySet(_CompanyQuerySetBase):
    """QuerySet for the Company model."""

    def accessible_to(self, user: User) -> CompanyQuerySet:
        """Return companies accessible to the given user.

        Args:
            user: The authenticated user.

        Returns:
            A filtered CompanyQuerySet.

        """
        if has_role(user, "admin"):
            return self

        person_pk = _get_user_person_pk(user)
        if person_pk is None:
            return self.none()

        if has_role(user, "undertaking_manager"):
            return self.filter(
                orders__versions__engagement_assignments__engagement__undertaking_assignments__undertaking__manager_id=person_pk
            ).distinct()

        if has_role(user, "person"):
            return self.filter(orders__versions__engagement_assignments__engagement__person_id=person_pk).distinct()

        return self.none()


CompanyManager = models.Manager.from_queryset(CompanyQuerySet)
