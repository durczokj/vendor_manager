# Using vendor_manager from Claude Desktop (MCP)

## What this is

`vendor_manager` exposes a small **Model Context Protocol (MCP)** server so you
can point an LLM client (Claude Desktop, ChatGPT desktop, etc.) at your own
vendor data and have it help you reconcile invoices, sanity-check costs, or
answer *"who did we bill this month for undertaking X?"* — using nothing but
your normal login.

The MCP server is a thin proxy. It has zero opinions of its own about who can
see what. Whatever role your account has in vendor_manager, that's exactly the
data the LLM will see. Nothing more.

## What you need

- A vendor_manager account with a password (Basic auth). If you only have SSO,
  ask an admin to set a password too.
- Claude Desktop (or any MCP-capable client). This guide uses Claude Desktop.

## Configure Claude Desktop

1. Open Claude Desktop → Settings → Developer → *Edit config*.
2. Add the following block under `mcpServers`, filling in your username and
   password. **These stay on your machine** — Claude Desktop forwards them to
   the MCP server on each call.

    ```jsonc
    {
      "mcpServers": {
        "vendor-manager": {
          "type": "http",
          "url": "https://vendor-manager-mcp.durczok.ovh/mcp/",
          "headers": {
            "Authorization": "Basic <base64(username:password)>"
          }
        }
      }
    }
    ```

    To generate the header value:

    ```bash
    printf '%s' 'your-username:your-password' | base64
    ```

3. Restart Claude Desktop. You should see four tools appear in the tool
   picker:

    | Tool                 | Purpose                                                          |
    |----------------------|------------------------------------------------------------------|
    | `list_cost_lines`    | One row per (engagement, day), all dimensions on every row.       |
    | `list_entity_options`| The persons / companies / orders / undertakings you can see.      |
    | `describe_api`       | Returns the OpenAPI schema — lists every endpoint the API exposes.|
    | `vm_api_request`     | Calls any vendor_manager endpoint (RBAC still applies per request).|

    `describe_api` + `vm_api_request` together let the LLM reach the full
    vendor_manager REST surface without any extra configuration.

## Worked example — reconciling an invoice

You have a July 2026 invoice from *Acme Corp* totalling €18 240. You want to
know which people and undertakings that came from.

Ask Claude:

> Pull cost lines from vendor_manager for July 2026 filtered to Acme Corp. Group
> the total by person and by undertaking and tell me if 18 240 matches.

Claude will call:

```json
{
  "tool": "list_cost_lines",
  "arguments": {
    "date_from": "2026-07-01",
    "date_to":   "2026-07-31",
    "company_ids": [ /* Acme Corp id, from list_entity_options */ ]
  }
}
```

and get back rows like:

```json
{
  "date": "2026-07-03",
  "cost": 520.0,
  "person_id": "P00042",
  "person_name": "Jakub Durczok",
  "order_id": 8001,
  "order_name": "Order 8001",
  "company_id": 9001,
  "company_name": "Acme Corp",
  "undertaking_id": 5001,
  "undertaking_name": "Undertaking 5001",
  "percentage": 1.0,
  "daily_rate": 520.0,
  "fte": 1.0,
  "is_working_day": true
}
```

which it can sum locally and diff against the invoice.

## Data scope and privacy

- The MCP server only sees what your role can see in vendor_manager. Every
  request re-checks the RBAC rules; there is no cached "trusted" view.
- Your Basic credentials never touch the MCP server's memory beyond a single
  request — the server holds no session store and no token cache.
- The MCP server never persists anything server-side (all four tools are
  stateless request/response wrappers). `vm_api_request` in particular can
  write, but only if the caller's role allows it — Django enforces RBAC on
  every call.

## Troubleshooting

| Symptom (from Claude)                                            | What's wrong                                                                                              |
|------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| "vendor_manager rejected the credentials (HTTP 401)."            | Your Basic header is missing or wrong. Re-base64 `username:password` and update Claude Desktop config.    |
| "vendor_manager rejected the request (HTTP 403). Role does not…" | You're authenticated but your role can't see that data. Ask for a broader role or narrow the query.       |
| "Requested span of N days exceeds the 400-day cap."              | Your `date_from`/`date_to` window is too wide. Split the request into calendar months or quarters.        |
| Tool `vm_api_request` missing.                                   | The MCP container image is stale. Pull the current image — `vm_api_request` and `describe_api` ship in every build. |
| Rate-limit `HTTP 429`.                                           | You're above 60 requests/minute against the MCP endpoint. Slow the conversation down.                     |

## Under the hood

- Transport: MCP Streamable HTTP, path `/mcp/`.
- Backend: the full [`/api/v1/`](../api-reference/using-the-api.md) surface;
  the two cost tools are convenience wrappers around
  `/dashboards/cost-lines/` and `/dashboards/entity-options/`.
- Auth: HTTP Basic (satisfies FR‑22).
- Deployment: `deploy/k8s/deployment-mcp.yaml` in this repo, Service/Ingress in
  the `vm` platform repo (`apps/vendor-manager-mcp/base/`).
