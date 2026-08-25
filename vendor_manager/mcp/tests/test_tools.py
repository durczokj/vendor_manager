"""Tests for the MCP tool wrappers.

These call the tool functions directly (bypassing FastMCP's registration)
so we can exercise the outbound HTTP path in isolation.
"""

from __future__ import annotations

import httpx
import pytest

from vendor_manager.mcp.client import VmApiAuthError, VmApiBadRequestError
from vendor_manager.mcp.tools.api_request import vm_api_request
from vendor_manager.mcp.tools.describe_api import describe_api


@pytest.mark.asyncio
async def test_vm_api_request_forwards_get_with_auth(api_client, mocked_api, patched_authorization):
    """The passthrough forwards the caller's Authorization header verbatim."""
    route = mocked_api.get("/people/").mock(return_value=httpx.Response(200, json=[{"id": "P1"}]))
    result = await vm_api_request(api_client, method="get", path="/people/")
    assert result == [{"id": "P1"}]
    assert route.called
    assert route.calls.last.request.headers["authorization"] == patched_authorization


@pytest.mark.asyncio
async def test_vm_api_request_posts_body(api_client, mocked_api, patched_authorization):
    """POSTs send the body Django expects and return the parsed response."""
    payload = {
        "date_from": "2026-07-01",
        "date_to": "2026-07-02",
        "company_ids": [9001],
        "person_ids": [],
    }
    route = mocked_api.post("/dashboards/cost-lines/").mock(
        return_value=httpx.Response(
            200,
            json={"date_from": "2026-07-01", "date_to": "2026-07-02", "count": 0, "rows": []},
        )
    )
    result = await vm_api_request(api_client, method="POST", path="/dashboards/cost-lines/", body=payload)
    assert result["count"] == 0
    assert route.called
    import json

    body = json.loads(route.calls.last.request.content)
    assert body == payload


@pytest.mark.asyncio
async def test_vm_api_request_401_bubbles_up(api_client, mocked_api, patched_authorization):
    """Auth failures at Django surface as VmApiAuthError from the tool."""
    mocked_api.get("/people/").mock(return_value=httpx.Response(401, json={"detail": "nope"}))
    with pytest.raises(VmApiAuthError):
        await vm_api_request(api_client, method="GET", path="/people/")


@pytest.mark.asyncio
async def test_vm_api_request_400_bubbles_up(api_client, mocked_api, patched_authorization):
    """400s from Django surface as VmApiBadRequestError with the server's detail."""
    mocked_api.post("/dashboards/cost-lines/").mock(
        return_value=httpx.Response(400, json={"detail": "Requested span of 800 days exceeds the 400-day cap"})
    )
    with pytest.raises(VmApiBadRequestError, match="400-day cap"):
        await vm_api_request(
            api_client,
            method="POST",
            path="/dashboards/cost-lines/",
            body={"date_from": "2024-01-01", "date_to": "2026-12-31"},
        )


@pytest.mark.asyncio
async def test_vm_api_request_uppercases_method(api_client, mocked_api, patched_authorization):
    """Lowercase method names are normalised before calling out."""
    route = mocked_api.get("/people/").mock(return_value=httpx.Response(200, json=[]))
    await vm_api_request(api_client, method="get", path="/people/")
    assert route.called


@pytest.mark.asyncio
async def test_describe_api_returns_openapi_schema(api_client, mocked_api, patched_authorization):
    """`describe_api` fetches `/schema/` and returns the parsed OpenAPI dict."""
    schema = {"openapi": "3.0.3", "info": {"title": "vendor_manager", "version": "1.0"}, "paths": {}}
    route = mocked_api.get("/schema/").mock(return_value=httpx.Response(200, json=schema))
    result = await describe_api(api_client)
    assert result == schema
    assert route.called
