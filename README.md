# Vendor Manager

A Django application for managing vendors, contracts, orders, engagements, and people
within an organisation. It exposes a browsable REST API (Django REST Framework) and a
Django-template UI, with role-based access control for Admin, UndertakingManager, and
Person personas.

For architecture, API reference, deployment, roles, and everything else see the
**[project docs](docs/index.md)**.

## Run locally (SQLite, no Docker)

```bash
pip install -r requirements.txt -r requirements-dev.txt
export DJANGO_DEBUG=true DJANGO_SECRET_KEY=dev DATABASE_ENGINE=sqlite
python manage.py migrate && python manage.py runserver
```

> Note: `VAR=value cmd` only sets vars for that single command, so the previous
> one-liner ran `runserver` without them and it failed to start (or started with
> `DEBUG=False`). `export` fixes that for the whole shell session.

Open <http://localhost:8000>. Full local-dev guide is at
[docs/developer-guide/local-dev.md](docs/developer-guide/local-dev.md).

## Run the MCP server locally

The MCP server (`vendor_manager/mcp/`) is a separate process that proxies an
LLM client (e.g. Claude Desktop) into the vendor_manager REST API. It has its
own runtime deps and its own image (`Dockerfile.mcp`); Django doesn't import
it and it doesn't import Django.

```bash
pip install -r requirements-mcp.txt
VM_API_BASE_URL=http://localhost:8000/api/v1 \
MCP_PORT=8100 \
python -m vendor_manager.mcp.server
```

`curl http://localhost:8100/healthz` should return `200`. See
[docs/user-guide/mcp.md](docs/user-guide/mcp.md) for the Claude Desktop config.

## License

MIT
