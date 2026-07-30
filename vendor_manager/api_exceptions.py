"""API exception helpers."""

from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import NotAuthenticated, ValidationError
from rest_framework.settings import api_settings
from rest_framework.views import exception_handler


def drf_exception_handler(exc: Exception, context: dict[str, object]):
    """Return DRF-standard error responses for framework and Django exceptions.

    Args:
        exc: Raised exception.
        context: DRF exception context.

    Returns:
        DRF response when handled, otherwise ``None``.
    """
    if isinstance(exc, DjangoValidationError):
        detail = exc.message_dict if hasattr(exc, "message_dict") else {api_settings.NON_FIELD_ERRORS_KEY: exc.messages}
        exc = ValidationError(detail=detail)

    response = exception_handler(exc, context)
    if response is not None and isinstance(exc, NotAuthenticated):
        response.status_code = 401
        response["WWW-Authenticate"] = 'Basic realm="api"'
    return response
