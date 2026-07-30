# Getting Started

Get Vendor Manager running locally in a few minutes.

## Prerequisites

- Python 3.13
- `pip`
- Docker (optional — only needed for Mode A with a real PostgreSQL database)

## Mode A — Compose DB + host app (recommended for development)

This mode starts **only PostgreSQL** in Docker; the Django app runs on the host so that
you keep fast reloads and access to your local debugger.

```bash
# 1. Start the database
docker compose up -d

# 2. Install Python dependencies
pip install -r requirements.txt -r requirements-dev.txt

# 3. Apply migrations
python manage.py migrate

# 4. Create a superuser
python manage.py createsuperuser

# 5. Start the development server
python manage.py runserver
```

Open <http://localhost:8000> in your browser.

## Mode B — Pure SQLite (no Docker at all)

Use this mode for quick experiments or in CI-like environments where Docker is not available.

```bash
# 1. Install Python dependencies
pip install -r requirements.txt -r requirements-dev.txt

# 2. Apply migrations (SQLite dev DB)
DJANGO_DEBUG=true DJANGO_SECRET_KEY=dev DATABASE_ENGINE=sqlite \
  python manage.py migrate

# 3. Create a superuser
DJANGO_DEBUG=true DJANGO_SECRET_KEY=dev DATABASE_ENGINE=sqlite \
  python manage.py createsuperuser

# 4. Start the development server
DJANGO_DEBUG=true DJANGO_SECRET_KEY=dev DATABASE_ENGINE=sqlite \
  python manage.py runserver
```

Open <http://localhost:8000> in your browser.

## Next steps

- See [Local dev](local-dev.md) for the full local development guide (tests, linting,
  sample data seeding).
- See [Architecture](architecture.md) to understand how the codebase is structured.
- See [API reference](/docs/api/) to explore the REST API interactively.
