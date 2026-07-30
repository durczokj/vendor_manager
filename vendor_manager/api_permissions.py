"""DRF permission classes for the vendor_manager project."""

from __future__ import annotations

import logging
from typing import Any

from django.contrib.auth.models import User
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from vendor_manager.utils.check_user_person_assignment import (
    NoPersonAssignedToUser,
    check_user_person_assignment,
)

logger = logging.getLogger(__name__)


class HasLinkedPerson(BasePermission):
    """Require the authenticated user to have exactly one linked Person.

    Unauthenticated requests fall through to the standard 401 path via
    ``IsAuthenticated`` (which must also be present in
    ``DEFAULT_PERMISSION_CLASSES``).  Authenticated users whose ``Person``
    record has been unlinked or deleted receive ``403 Forbidden`` with the
    error message mandated by ``FR-23``.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        """Return True iff the user is authenticated and has a linked Person.

        Args:
            request: The incoming DRF request.
            view: The view being accessed.

        Returns:
            ``True`` when the user is authenticated and a linked ``Person``
            exists (or the user holds an exempted role such as *admin*).
            ``False`` for unauthenticated requests (triggering the standard
            401 challenge handled by ``IsAuthenticated``).

        Raises:
            PermissionDenied: When an authenticated user lacks a linked
                ``Person`` record.
        """
        if not isinstance(request.user, User):
            return False
        try:
            check_user_person_assignment(request.user)
            return True
        except NoPersonAssignedToUser as exc:
            logger.debug("API access blocked for user '%s': %s", request.user.get_username(), exc)
            raise PermissionDenied(
                detail=f"User '{request.user.get_username()}' is not assigned to any person."
            ) from exc
