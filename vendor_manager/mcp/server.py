"""FastMCP server entrypoint for vendor_manager.

Run with ``python -m vendor_manager.mcp.server``. Streamable HTTP transport
listens on ``0.0.0.0:8000`` by default (override with ``MCP_HOST`` /
``MCP_PORT``). Two tools are registered — :func:`describe_api` for
endpoint discovery and :func:`vm_api_request` as the workhorse — and both
forward the caller's ``Authorization: Basic …`` header verbatim to the
Django API, so Django's RBAC is the sole authority on what data comes
back.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from vendor_manager.mcp.client import VmApiClient
from vendor_manager.mcp.tools.api_request import vm_api_request as _vm_api_request
from vendor_manager.mcp.tools.describe_api import describe_api as _describe_api

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    """Configure structured JSON logging for the MCP server."""
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    try:
        from pythonjsonlogger.json import JsonFormatter

        handler: logging.Handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        root = logging.getLogger()
        root.handlers = [handler]
        root.setLevel(log_level)
    except ImportError:
        # Plain logging is fine for local dev; JSON is only required in-cluster.
        logging.basicConfig(level=log_level)


def build_app(client: VmApiClient | None = None) -> FastMCP:
    """Build the FastMCP application.

    Args:
        client: Optional pre-built :class:`VmApiClient` (tests inject a
            fake here). In production a fresh client is created lazily so
            each tool call opens its own connection pool.

    Returns:
        A fully configured :class:`FastMCP` app.
    """
    app: FastMCP = FastMCP(name="vendor-manager-mcp")
    api_client = client or VmApiClient()

    @app.custom_route("/healthz", methods=["GET"], include_in_schema=False)
    async def healthz(_request: Request) -> JSONResponse:
        """Liveness / readiness probe for Kubernetes."""
        return JSONResponse({"status": "ok"})

    @app.tool()
    async def describe_api() -> dict[str, Any]:
        """Return the vendor_manager OpenAPI schema.

        Call this first when you don't know which endpoint to hit — it
        lists every path, method, parameter, and response shape the
        vendor_manager REST API supports. Use the result to pick the
        right ``method`` / ``path`` / ``params`` / ``body`` for
        :func:`vm_api_request`.
        """
        return await _describe_api(api_client)

    @app.tool()
    async def vm_api_request(
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        """Call any vendor_manager API endpoint.

        Combined with :func:`describe_api`, this covers the full REST
        surface. RBAC is enforced on the Django side per request, so a
        successful call is one the caller was already entitled to make.

        Args:
            method: HTTP verb (``GET``, ``POST``, ``PATCH``, ``DELETE``, …).
            path: Path under ``/api/v1/`` — e.g. ``"/people/"`` or
                ``"/engagements/42/"``. Leading slash optional.
            params: Optional query-string parameters.
            body: Optional JSON body (for ``POST`` / ``PATCH`` / ``PUT``).
        """
        return await _vm_api_request(
            api_client,
            method=method,
            path=path,
            params=params,
            body=body,
        )

    return app


def main() -> None:  # pragma: no cover - thin entrypoint
    """Run the MCP server over Streamable HTTP.

    Binds to ``MCP_HOST`` (default ``0.0.0.0``) and ``MCP_PORT`` (default
    ``8000``); override the port locally if Django's ``runserver`` already
    holds ``:8000``.
    """
    _configure_logging()
    app = build_app()
    host = os.environ.get("MCP_HOST", "0.0.0.0")  # noqa: S104 - container binds all interfaces
    port = int(os.environ.get("MCP_PORT", "8000"))
    app.run(transport="http", host=host, port=port)


if __name__ == "__main__":  # pragma: no cover
    main()
