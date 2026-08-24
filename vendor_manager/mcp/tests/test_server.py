"""Tests for :func:`vendor_manager.mcp.server.build_app`.

Verifies tool registration; does not spin up the Streamable HTTP transport.
"""

from __future__ import annotations

from typing import Any

import pytest

from vendor_manager.mcp.client import VmApiClient
from vendor_manager.mcp.server import build_app


@pytest.fixture
def stub_client(monkeypatch: pytest.MonkeyPatch) -> VmApiClient:
    """Return a VmApiClient bound to a dummy URL (no outbound calls in these tests)."""
    monkeypatch.setenv("VM_API_BASE_URL", "http://vm-test.internal/api/v1")
    return VmApiClient()


async def _tool_names(app: Any) -> set[str]:
    tools = await app.list_tools()
    return {t.name for t in tools}


@pytest.mark.asyncio
async def test_all_tools_registered(stub_client):
    """The MCP surface is exactly `describe_api` + `vm_api_request`."""
    app = build_app(client=stub_client)
    names = await _tool_names(app)
    assert names == {"describe_api", "vm_api_request"}
