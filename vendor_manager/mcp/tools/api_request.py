"""`vm_api_request` — generic passthrough tool.

Always registered. Combined with :mod:`vendor_manager.mcp.tools.describe_api`
(which returns the OpenAPI schema so the LLM can discover endpoints) it
covers the full vendor_manager REST surface. Django's RBAC applies to every
outbound request; the MCP process holds no credentials of its own.
"""

from __future__ import annotations

from typing import Any

from vendor_manager.mcp.client import VmApiClient
from vendor_manager.mcp.context import get_authorization_header


async def vm_api_request(
    client: VmApiClient,
    *,
    method: str,
    path: str,
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
) -> Any:
    """Call an arbitrary vendor_manager API endpoint.

    Args:
        client: The :class:`VmApiClient` used for the outbound HTTP call.
        method: HTTP verb (``GET``, ``POST``, …).
        path: Path relative to the API root (leading slash optional).
        params: Optional query-string parameters.
        body: Optional JSON body.

    Returns:
        The decoded JSON response.
    """
    authorization = get_authorization_header()
    return await client.request(
        method.upper(),
        path,
        authorization=authorization,
        params=params,
        json=body,
    )
