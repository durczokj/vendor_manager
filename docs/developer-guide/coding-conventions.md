# Coding conventions

The rules below are how the codebase stays reviewable. They mirror the guardrails in
`.github/copilot-instructions.md`. When a new module lands, run through this checklist.

## Layering

- **Models** hold structure, DB-level constraints, and single-model invariants in
  `clean()` (per NFR‑1, NFR‑8). They MUST NOT know about HTTP, HTML, or DRF.
- **Managers** (`<app>/managers.py`) hold `QuerySet` subclasses. Every entity ships an
  `<Entity>QuerySet.accessible_to(user)` method (per FR‑28, NFR‑7). All object-level
  access flows through it — no per-view filtering.
- **Selectors** (`<app>/selectors.py`) hold read-only computations. Every function takes
  its inputs explicitly (no `self`), returns plain Python data or a `QuerySet`, and is
  wrapped in `select_related` / `prefetch_related` at the boundary (per NFR‑8).
- **Services** (`<app>/services.py`) hold write operations. Multi-step writes MUST be
  wrapped in `transaction.atomic()` (per NFR‑1). Both UI views and API viewsets call the
  same service — never bypass it (per NFR‑2, NFR‑3).
- **Views** (`<app>/views.py`) are thin Django CBVs. They validate a form, call a
  service, redirect. No business logic here.
- **Viewsets** (`<app>/api.py`) are thin DRF viewsets. They deserialize, call a service,
  serialize. `get_queryset` always returns `.accessible_to(self.request.user)`.

## Logging

- **No `print()` in application code** (per NFR‑27). Use
  `logging.getLogger(__name__)` and log at the appropriate level.
- Log lines are emitted to stdout as JSON (per NFR‑36, NFR‑37). The request middleware
  injects `user_id` / `request_id` on every record.
- Django's `django.request` and `django.security` loggers propagate to the shared
  handler.

## Type hints

- Every new module lands with `mypy --strict`-clean annotations (per NFR‑30).
- The strict scope is controlled by `[tool.mypy] files = [...]` in
  [`pyproject.toml`](https://github.com/durczokj/vendor_manager/blob/main/pyproject.toml). Add new modules to that list as they land.
- The whole-project sweep is P8; don't remove existing `# type: ignore` outside the
  P8.T3 / P8.T4 tasks. Every ignore comment MUST reference the phase that removes it
  (`# TODO(P8): …`).

## Docstrings

- Google-style docstrings on public functions, methods, and classes where ruff's `D`
  rules apply.
- The one-line summary states *what*, not *how*. If the *why* is non-obvious, add a
  paragraph.
- Do not restate the type signature in the docstring.

## Migrations

- Additive. Never edit an applied migration (per NFR‑20).
- The squashed initial per app (from P1.T2) is the historical base. Add new migrations
  on top of it.
- Every `RunPython` MUST include a `reverse_code` (per NFR‑22).
- Migrations MUST pass on both SQLite and PostgreSQL (per NFR‑21). No MSSQL, no
  `mssql-django` (per NFR‑23).

## URL naming

- Per FR‑49: hyphenated, plural, kebab-case where relevant.
- Django URL names follow the DRF convention `<basename>-list` / `<basename>-detail` /
  `<basename>-<action>` (per FR‑50). Set `basename=` explicitly on the router if the
  default doesn't match.
- Rename endpoints only as you touch them; do not preemptively rename to avoid churn.

## Deletion flows

- Every UI delete uses an intermediate `_confirm_delete.html` page (per FR‑40). No
  inline `onclick="confirm(…)"` handlers.
- API delete verbs are the standard DRF `DELETE`, guarded by `accessible_to(user)`.

## Database engines

- Only **PostgreSQL** and **SQLite** are supported (per NFR‑21).
- `settings.DATABASE_ENGINE` accepts only `"sqlite"` or `"postgresql"`. No branching for
  other engines.
- Any migration or query MUST work on both.

## Secrets and settings

- Every secret comes from environment; no in-repo default for `DJANGO_SECRET_KEY` (per
  NFR‑12).
- `DEBUG` defaults to `False` when the env var is unset or empty (per NFR‑13). Boot
  fails loudly if a production secret is missing.
- `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` are env-configured (per NFR‑14).

## Dependencies

- Runtime deps in `requirements.txt` (pinned). Dev deps in `requirements-dev.txt`.
- Docs-build deps in `requirements-docs.txt`.
- Never introduce a new top-level dependency without adding it to the right requirements
  file and justifying it in the commit message.

## Commits and PRs

- Reference the task ID in commit titles: `P<phase>.T<n>: <one-line summary>`.
- Reference every FR / NFR the change satisfies in the commit body.
- Small, self-contained commits — each one should leave CI green on its own.
- Never mix a mechanical refactor with a behavior change in one commit.

## Verify loop

Run this before every push. It mirrors CI.

```bash
ruff check .
ruff format --check .
mypy
DJANGO_DEBUG=true DJANGO_SECRET_KEY=dev DATABASE_ENGINE=sqlite pytest --cov
DJANGO_DEBUG=false DJANGO_SECRET_KEY="ci-only-secret-key-32bytes-of-padding-not-a-real-secret-value-xyz" DJANGO_ALLOWED_HOSTS=localhost DATABASE_ENGINE=sqlite python manage.py check --deploy
mkdocs build --strict
```

## How to add a new entity

The end-to-end checklist:

1. **Model** — `<app>/models.py`. Enforce single-model invariants in `clean()`.
2. **Manager** — `<app>/managers.py`. Add `<Entity>QuerySet` with `accessible_to(user)`.
3. **Service** — `<app>/services.py`. One function per write operation, transactional.
4. **Selector** — `<app>/selectors.py`. One function per read-computation.
5. **Serializer** — `<app>/serializers.py`. Explicit `fields = [...]` per FR‑29.
6. **Viewset** — `<app>/api.py`. `get_queryset` calls `.accessible_to(...)`.
7. **Filter** — `<app>/filters.py`. `<Entity>FilterSet`.
8. **UI view** — `<app>/views.py`. CBV that delegates to the service.
9. **UI form** — `<app>/forms.py`. Explicit `fields = [...]`.
10. **UI table** — `<app>/tables.py`. django-tables2 `<Entity>Table`.
11. **UI URLs** — `<app>/urls.py`. Named per FR‑50.
12. **Nav entry** — `vendor_manager/navigation.py`.
13. **Factories + tests** — `<app>/tests/factories.py`, plus tests for model, service,
    API, permission (per NFR‑16).
14. **Docs** — a User Guide page under `docs/user-guide/` (per FR‑52) if the entity is
    end-user visible.

## Related pages

- [Architecture](architecture.md) — how the layers interact at runtime.
- [Testing](testing.md) — factories, permission matrix, coverage gates.
- [Local dev](local-dev.md) — the verify loop above, in more detail.
