"""Helpers shared by the MCP tools.

The tools sit on top of :class:`vendor_manager.mcp.client.VmApiClient` and
extract the incoming HTTP ``Authorization`` header via a single helper so
that tests can stub it in one place.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from vendor_manager.mcp.client import VmApiAuthError

logger = logging.getLogger(__name__)


def get_authorization_header() -> str:
    """Return the incoming MCP request's ``Authorization`` header value.

    Uses :func:`fastmcp.server.dependencies.get_http_headers` so it only
    works inside a live FastMCP tool call. Tests patch this function.

    Falls back to the ``VM_API_AUTH`` environment variable when set. This
    fallback is intended for local development where the MCP client cannot
    forward the ``Authorization`` header (e.g. ``mcp-remote`` bridges).
    Do NOT set ``VM_API_AUTH`` in multi-user deployments — every caller
    would inherit that identity.

    Raises:
        VmApiAuthError: If no header is present and no fallback is configured.
    """
    from fastmcp.server.dependencies import get_http_headers

    # fastmcp strips `authorization` from get_http_headers() by default; opt in.
    headers: dict[str, Any] = get_http_headers(include={"authorization"}) or {}
    logger.debug("mcp incoming header names: %s", sorted(headers.keys()))
    # Header names come through lowercase from Starlette.
    auth = headers.get("authorization") or headers.get("Authorization")
    if not auth:
        fallback = os.environ.get("VM_API_AUTH")
        if fallback:
            logger.info("Using VM_API_AUTH fallback (dev-only, single-identity).")
            return fallback
        raise VmApiAuthError(
            "The MCP request has no Authorization header. Configure HTTP Basic "
            "auth in your MCP client (username + password of your "
            "vendor_manager account), or set VM_API_AUTH on the server for "
            "single-user local development.",
            status_code=401,
        )
    return str(auth)
