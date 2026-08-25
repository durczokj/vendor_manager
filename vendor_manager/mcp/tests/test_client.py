"""Tests for :mod:`vendor_manager.mcp.client`."""

from __future__ import annotations

import httpx
import pytest

from vendor_manager.mcp.client import (
    VmApiAuthError,
    VmApiBadRequestError,
    VmApiClient,
    VmApiError,
)


@pytest.mark.asyncio
async def test_request_forwards_authorization_header(api_client, mocked_api):
    """The raw MCP Authorization header must reach Django unchanged."""
    route = mocked_api.get("/dashboards/entity-options/").mock(return_value=httpx.Response(200, json={"persons": []}))
    result = await api_client.request(
        "GET",
        "/dashboards/entity-options/",
        authorization="Basic YWxpY2U6cHc=",
    )
    assert result == {"persons": []}
    assert route.called
    sent = route.calls.last.request
    assert sent.headers["authorization"] == "Basic YWxpY2U6cHc="


@pytest.mark.asyncio
async def test_missing_authorization_raises_auth_error(api_client):
    """A tool called with an empty header fails fast without hitting the API."""
    with pytest.raises(VmApiAuthError):
        await api_client.request("GET", "/dashboards/entity-options/", authorization="")


@pytest.mark.asyncio
async def test_401_maps_to_auth_error(api_client, mocked_api):
    """HTTP 401 from Django surfaces as :class:`VmApiAuthError`."""
    mocked_api.get("/dashboards/entity-options/").mock(return_value=httpx.Response(401, json={"detail": "nope"}))
    with pytest.raises(VmApiAuthError) as excinfo:
        await api_client.request("GET", "/dashboards/entity-options/", authorization="Basic bad")
    assert excinfo.value.status_code == 401
    assert "Basic" in str(excinfo.value)


@pytest.mark.asyncio
async def test_403_maps_to_auth_error(api_client, mocked_api):
    """HTTP 403 surfaces as :class:`VmApiAuthError` with role-scope wording."""
    mocked_api.get("/dashboards/entity-options/").mock(return_value=httpx.Response(403, json={"detail": "role"}))
    with pytest.raises(VmApiAuthError) as excinfo:
        await api_client.request("GET", "/dashboards/entity-options/", authorization="Basic ok")
    assert excinfo.value.status_code == 403
    assert "role" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_400_maps_to_bad_request(api_client, mocked_api):
    """HTTP 400 surfaces as :class:`VmApiBadRequestError` and quotes the body."""
    mocked_api.post("/dashboards/cost-lines/").mock(return_value=httpx.Response(400, json={"detail": "span too large"}))
    with pytest.raises(VmApiBadRequestError) as excinfo:
        await api_client.request(
            "POST",
            "/dashboards/cost-lines/",
            authorization="Basic ok",
            json={"date_from": "2026-01-01", "date_to": "2027-12-31"},
        )
    assert excinfo.value.status_code == 400
    assert "span too large" in str(excinfo.value)


@pytest.mark.asyncio
async def test_500_maps_to_generic_error(api_client, mocked_api):
    """Unexpected 5xx maps to :class:`VmApiError` (not the auth subclass)."""
    mocked_api.get("/dashboards/entity-options/").mock(return_value=httpx.Response(500, text="boom"))
    with pytest.raises(VmApiError) as excinfo:
        await api_client.request("GET", "/dashboards/entity-options/", authorization="Basic ok")
    assert not isinstance(excinfo.value, (VmApiAuthError, VmApiBadRequestError))
    assert excinfo.value.status_code == 500


def test_missing_base_url_raises(monkeypatch):
    """The client refuses to construct itself without a base URL."""
    monkeypatch.delenv("VM_API_BASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="VM_API_BASE_URL"):
        VmApiClient()


def test_base_url_env_is_used(monkeypatch):
    """When constructed without an explicit base URL, env is consulted."""
    monkeypatch.setenv("VM_API_BASE_URL", "http://from-env.local/api/v1/")
    client = VmApiClient()
    assert client.base_url == "http://from-env.local/api/v1"


@pytest.mark.asyncio
async def test_client_creates_ephemeral_when_none_injected(mocked_api, monkeypatch):
    """When no httpx client is provided, one is created and closed per call."""
    monkeypatch.setenv("VM_API_BASE_URL", "http://vm-test.internal/api/v1")
    mocked_api.get("/dashboards/entity-options/").mock(return_value=httpx.Response(200, json={"persons": []}))
    client = VmApiClient()
    result = await client.request("GET", "/dashboards/entity-options/", authorization="Basic ok")
    assert result == {"persons": []}
