# Local Development Guide

## Prerequisites

- Python 3.13
- Docker (optional, for running via `compose.yml`)
- A running PostgreSQL instance **or** `DATABASE_ENGINE=sqlite` for a lightweight SQLite dev DB

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# 2. Apply migrations (SQLite dev DB)
DJANGO_DEBUG=true DJANGO_SECRET_KEY=dev DATABASE_ENGINE=sqlite python manage.py migrate

# 3. Create a superuser
DJANGO_DEBUG=true DJANGO_SECRET_KEY=dev DATABASE_ENGINE=sqlite python manage.py createsuperuser

# 4. Start the development server
DJANGO_DEBUG=true DJANGO_SECRET_KEY=dev DATABASE_ENGINE=sqlite python manage.py runserver
```

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

See [`scripts/populate.md`](../scripts/populate.md) for the full entity list and
endpoint coverage matrix.

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
