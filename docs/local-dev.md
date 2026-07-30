# Local Development Guide

## Prerequisites

- Python 3.13
- Docker (optional — only needed for Mode A with a real PostgreSQL database)
- `pip`

## Dev mode A — Compose DB + host app (default)

Start **only PostgreSQL** in Docker; the Django app runs on the host for fast reloads and
easy debugging.

```bash
# 1. Start PostgreSQL
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

## Dev mode B — Pure SQLite (no Docker)

Run everything on the host using an SQLite database file. No containers required. Useful
for quick experiments and CI-like environments.

```bash
# 1. Install Python dependencies
pip install -r requirements.txt -r requirements-dev.txt

# 2. Apply migrations (SQLite dev DB)
DJANGO_DEBUG=true DJANGO_SECRET_KEY=dev DATABASE_ENGINE=sqlite python manage.py migrate

# 3. Create a superuser
DJANGO_DEBUG=true DJANGO_SECRET_KEY=dev DATABASE_ENGINE=sqlite python manage.py createsuperuser

# 4. Start the development server
DJANGO_DEBUG=true DJANGO_SECRET_KEY=dev DATABASE_ENGINE=sqlite python manage.py runserver
```

Open <http://localhost:8000> in your browser.

## Populating sample data

`scripts/populate.py` seeds a running instance with a realistic dataset via the
REST API.  It requires no Django imports — it is a pure HTTP client that can
target any accessible URL (local, staging, or post-deploy k3s).

### Basic invocation

```bash
python scripts/populate.py \
    --base-url http://localhost:8000 \
    --user admin \
    --password admin \
    --reset \
    --seed 42
```

| Flag | Default | Description |
|------|---------|-------------|
| `--base-url` | `http://localhost:8000` | Base URL of the running app |
| `--user` | *(required)* | HTTP Basic auth username (staff / superuser) |
| `--password` | *(required)* | HTTP Basic auth password |
| `--reset` | off | Delete all existing data **before** populating (safe for dev; do not use against production without care) |
| `--seed` | `42` | Integer seed — same seed → identical data every time |

### What gets created

See [`scripts/populate.md`](https://github.com/durczokj/vendor_manager/blob/main/scripts/populate.md)
for the full entity list and endpoint coverage matrix.

### Smoke-testing a deployment

Run the same command against the deployed URL to verify every API endpoint is
functional after a release:

```bash
python scripts/populate.py \
    --base-url https://staging.example.com \
    --user <admin> \
    --password <pw> \
    --reset \
    --seed 42
```

A clean run (exit 0) means all covered endpoints responded 2xx — the release is
functional.

## Running the test suite

```bash
DJANGO_DEBUG=true DJANGO_SECRET_KEY=dev DATABASE_ENGINE=sqlite pytest --cov
```

## Linting and type-checking

```bash
ruff check .
ruff format --check .
mypy
```

## Deployment check

```bash
DJANGO_DEBUG=false \
DJANGO_SECRET_KEY="ci-only-secret-key-32bytes-of-padding-not-a-real-secret-value-xyz" \
DJANGO_ALLOWED_HOSTS=localhost \
DATABASE_ENGINE=sqlite \
python manage.py check --deploy
```
