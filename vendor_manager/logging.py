"""Structured stdout logging for vendor_manager.

Provides:
  * ``RequestContextFilter`` — attaches ``user_id`` and ``request_id`` to every
    ``LogRecord``, sourcing them from a per-request contextvar that is populated
    by ``RequestContextMiddleware``.
  * ``RequestContextMiddleware`` — middleware that sets the contextvar for the
    duration of a request and clears it on the way out.

The formatter (``pythonjsonlogger.jsonlogger.JsonFormatter``) is configured in
``settings.LOGGING`` and picks up any extra attributes on the record, so no
explicit ``extra=`` at each log site is required.
"""

from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar
from typing import Any

from django.http import HttpRequest, HttpResponse

_UNSET = "-"

_request_id_var: ContextVar[str] = ContextVar("request_id", default=_UNSET)
_user_id_var: ContextVar[str] = ContextVar("user_id", default=_UNSET)


class RequestContextFilter(logging.Filter):
    """Attach ``user_id`` and ``request_id`` from contextvars to every record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.user_id = _user_id_var.get()
        record.request_id = _request_id_var.get()
        return True


class RequestContextMiddleware:
    """Populate the request context for the duration of a request.

    - ``request_id`` comes from the ``X-Request-Id`` header if the upstream sent
      one, otherwise a fresh UUID4. Downstream services / log aggregators can
      correlate on this value.
    - ``user_id`` is the authenticated user's primary key, or ``"-"`` for
      anonymous requests.
    """

    def __init__(self, get_response: Any) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex
        rid_token = _request_id_var.set(request_id)
        user = getattr(request, "user", None)
        uid_token = _user_id_var.set(
            str(user.pk) if user is not None and getattr(user, "is_authenticated", False) else _UNSET
        )
        try:
            response = self.get_response(request)
            response.headers["X-Request-Id"] = request_id
            return response
        finally:
            _request_id_var.reset(rid_token)
            _user_id_var.reset(uid_token)
