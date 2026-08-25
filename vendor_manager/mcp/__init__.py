"""MCP (Model Context Protocol) server for vendor_manager.

This package exposes a thin FastMCP wrapper around the vendor_manager REST
API. It does **not** import Django and holds no credentials of its own —
requests coming from an MCP client (Claude Desktop, etc.) carry an HTTP
Basic ``Authorization`` header which is forwarded verbatim to the Django
API on every outbound call (P11.T2, satisfies FR-63).
"""
