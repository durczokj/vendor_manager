"""HTTP client used by every MCP tool to reach the vendor_manager Django API.

The client is intentionally minimal:

* One outbound base URL, read from ``VM_API_BASE_URL`` (no default; the
  server refuses to start without it).
* The MCP ``Authorization`` header is forwarded verbatim; the client itself
  never reads credentials from disk or env.
* HTTP status codes from Django are mapped to :class:`VmApiError` variants
  so tool code can raise clear MCP-level errors without importing httpx.
"""

from __future__ import annotations

import os
from typing import Any

import httpx


class VmApiError(RuntimeError):
    """Base exception for vendor_manager API failures surfaced to the MCP tool."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialise the error.

        Args:
            message: Human-readable message returned to the MCP client.
            status_code: The upstream HTTP status code, if any.
        """
        super().__init__(message)
        self.status_code = status_code


class VmApiAuthError(VmApiError):
    """Raised when Django returns 401 or 403.

    401 => Basic credentials missing or wrong. 403 => authenticated but the
    role does not permit the requested data.
    """


class VmApiBadRequestError(VmApiError):
    """Raised when Django returns 400 (validation failure, span-cap, etc.)."""


def _resolve_base_url() -> str:
    """Return the configured ``VM_API_BASE_URL`` or raise a startup error."""
    base = os.environ.get("VM_API_BASE_URL", "").rstrip("/")
    if not base:
        raise RuntimeError(
            "VM_API_BASE_URL is not set. Point it at the in-cluster vendor_manager "
            "API, e.g. http://vendor-manager.prod.svc.cluster.local/api/v1."
        )
    return base


class VmApiClient:
    """Thin async httpx wrapper for the vendor_manager REST API.

    The ``authorization`` argument on every method is the raw value of the
    incoming MCP ``Authorization`` header (typically ``"Basic <b64>"``). It
    is forwarded to Django unchanged; the MCP process holds no credentials.
    """

    def __init__(
        self,
        base_url: str | None = None,
        *,
        client: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialise the client.

        Args:
            base_url: Base URL of the vendor_manager API. Defaults to the
                ``VM_API_BASE_URL`` environment variable.
            client: Optional pre-built ``httpx.AsyncClient``. Tests inject a
                ``respx`` mock through this parameter; production leaves it
                ``None`` so :meth:`request` creates one per call.
            timeout: Per-request timeout in seconds.
        """
        self.base_url = (base_url or _resolve_base_url()).rstrip("/")
        self._client = client
        self._timeout = timeout

    async def request(
        self,
        method: str,
        path: str,
        *,
        authorization: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """Perform an authenticated request against the vendor_manager API.

        Args:
            method: HTTP method (``"GET"``, ``"POST"``, …).
            path: Path relative to ``base_url`` (leading slash optional).
            authorization: The raw ``Authorization`` header from the MCP
                request. Forwarded verbatim.
            params: Optional query-string parameters.
            json: Optional JSON body.

        Returns:
            The decoded JSON response body.

        Raises:
            VmApiAuthError: On upstream 401 / 403.
            VmApiBadRequestError: On upstream 400.
            VmApiError: On any other non-2xx response.
        """
        if not authorization:
            raise VmApiAuthError(
                "No Authorization header on the MCP request. Configure Basic auth in your MCP client.",
                status_code=401,
            )

        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {"Authorization": authorization, "Accept": "application/json"}

        client = self._client
        owned = False
        if client is None:
            client = httpx.AsyncClient(timeout=self._timeout)
            owned = True

        try:
            response = await client.request(method, url, params=params, json=json, headers=headers)
        finally:
            if owned:
                await client.aclose()

        if response.status_code in (401, 403):
            raise VmApiAuthError(
                _describe_auth_failure(response.status_code, response.text),
                status_code=response.status_code,
            )
        if response.status_code == 400:
            raise VmApiBadRequestError(
                _describe_bad_request(response.text),
                status_code=400,
            )
        if response.status_code >= 400:
            raise VmApiError(
                f"vendor_manager API returned HTTP {response.status_code}: {response.text[:200]}",
                status_code=response.status_code,
            )
        return response.json()


def _describe_auth_failure(status_code: int, body: str) -> str:
    """Return a human-readable message for a 401/403 upstream response."""
    if status_code == 401:
        return "vendor_manager rejected the credentials (HTTP 401). Check your Basic username/password."
    return (
        "vendor_manager rejected the request (HTTP 403). Your account is authenticated but its "
        "role does not permit that data."
    )


def _describe_bad_request(body: str) -> str:
    """Return a human-readable message for an upstream 400 response."""
    snippet = body.strip().replace("\n", " ")[:300]
    return f"vendor_manager rejected the request (HTTP 400): {snippet}"
