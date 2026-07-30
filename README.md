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
DJANGO_DEBUG=true DJANGO_SECRET_KEY=dev DATABASE_ENGINE=sqlite python manage.py migrate && python manage.py runserver
```

Open <http://localhost:8000>. Full local-dev guide (including the Compose+PostgreSQL
mode) is at [docs/local-dev.md](docs/local-dev.md).

## License

MIT
