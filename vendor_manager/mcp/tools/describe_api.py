"""`describe_api` — return the vendor_manager OpenAPI schema.

The LLM should call this first when it doesn't know which endpoint to hit.
The response is the same JSON that ``GET /api/v1/schema/`` returns, which
enumerates every path, method, parameter, and response the vendor_manager
REST API supports.
"""

from __future__ import annotations

from typing import Any

from vendor_manager.mcp.client import VmApiClient
from vendor_manager.mcp.context import get_authorization_header


async def describe_api(client: VmApiClient) -> dict[str, Any]:
    """Fetch and return the vendor_manager OpenAPI schema.

    Args:
        client: The :class:`VmApiClient` used for the outbound HTTP call.

    Returns:
        The decoded OpenAPI schema JSON (a dict).

    Raises:
        VmApiAuthError: On 401 / 403 from Django.
    """
    authorization = get_authorization_header()
    result = await client.request(
        "GET",
        "/schema/",
        authorization=authorization,
    )
    return dict(result)
