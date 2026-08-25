"""Shared fixtures for MCP tests.

Every test that exercises a tool goes through :func:`patched_authorization`,
so the ``Authorization`` header is deterministic regardless of whether the
tool is called inside a live FastMCP context or via ``asyncio.run``.
"""

from __future__ import annotations

from collections.abc import Iterator

import httpx
import pytest
import respx

from vendor_manager.mcp import context as ctx_module
from vendor_manager.mcp.client import VmApiClient

BASE_URL = "http://vm-test.internal/api/v1"


@pytest.fixture
def api_client() -> VmApiClient:
    """Return a VmApiClient bound to a stable fake URL for respx to match."""
    return VmApiClient(base_url=BASE_URL, client=httpx.AsyncClient())


@pytest.fixture
def patched_authorization(monkeypatch: pytest.MonkeyPatch) -> str:
    """Stub :func:`vendor_manager.mcp.context.get_authorization_header`.

    Returns the value the tools will see so tests can assert pass-through.
    """
    header = "Basic dXNlcjpwYXNz"  # user:pass

    def _fake() -> str:
        return header

    monkeypatch.setattr(ctx_module, "get_authorization_header", _fake)
    # Also patch it inside each tool module that imported the symbol directly.
    for mod_name in (
        "vendor_manager.mcp.tools.describe_api",
        "vendor_manager.mcp.tools.api_request",
    ):
        import importlib

        mod = importlib.import_module(mod_name)
        monkeypatch.setattr(mod, "get_authorization_header", _fake)
    return header


@pytest.fixture
def mocked_api() -> Iterator[respx.MockRouter]:
    """Yield a respx router scoped to :data:`BASE_URL`."""
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        yield router
