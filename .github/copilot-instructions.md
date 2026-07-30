# Copilot instructions for `vendor_manager`

You are working on the **vendor_manager** Django application. Every task you receive maps to one entry in [docs/IMPLEMENTATION_PLAN.md](../docs/IMPLEMENTATION_PLAN.md), which itself is derived from [docs/REQUIREMENTS.md](../docs/REQUIREMENTS.md).

## Contract with the reviewer

1. **Read the linked task first.** Every issue you're assigned has a task ID like `P3.T2`. Find that task in `docs/IMPLEMENTATION_PLAN.md`, read its `Satisfies` / `Do` / `Acceptance` bullets, and do exactly what they say. Nothing more.
2. **Do not touch scope outside the task.** If you spot a bug or a lint issue that isn't in your task's `Do`, leave it. Open a follow-up issue in the PR description instead.
3. **A task is done when every bullet under `Acceptance` is verifiably satisfied.** If you cannot satisfy one, stop and explain in the PR description.
4. **Reference the task ID in your commit messages and PR title.** Format: `P3.T2: <one-line summary>`.
5. **Reference every FR-/NFR- number** your change satisfies in the commit body.

## Repository shape

- Django 5.1 project. Python 3.13 (matches `Dockerfile`).
- Apps: `companies`, `contracts`, `people`, `orders`, `undertakings`, `engagements`, `leaves`, plus the `vendor_manager` project package and `dashboards/` (going away in Phase 5).
- Tooling source of truth: `pyproject.toml` (ruff, mypy, pytest, coverage).
- Runtime deps in `requirements.txt`; dev deps in `requirements-dev.txt`.
- CI: `.github/workflows/ci.yaml`. CD: `.github/workflows/deploy.yaml` (do NOT edit CD unless the task explicitly says so; production is k3s).

## Local verification loop before pushing

Run this sequence and make it clean. If any step fails, fix and re-run.

```bash
ruff check .
ruff format --check .
mypy
DJANGO_DEBUG=true DJANGO_SECRET_KEY=dev DATABASE_ENGINE=sqlite pytest --cov
DJANGO_DEBUG=false DJANGO_SECRET_KEY="ci-only-secret-key-32bytes-of-padding-not-a-real-secret-value-xyz" DJANGO_ALLOWED_HOSTS=localhost DATABASE_ENGINE=sqlite python manage.py check --deploy
```

## Rules that apply to every task

- **No `print()` in application code.** Use `logging.getLogger(__name__)`.
- **No new hand-rolled auth.** DRF handles authentication (Basic + Session per FR‑22, NFR‑10). Django's `LoginView` handles the UI login.
- **No hidden business logic in views.** Business logic goes in `<app>/services.py`; read-only computations go in `<app>/selectors.py`; querysets go in model `Manager`s. See Phase 2.
- **All new code must pass `mypy --strict`.** Legacy modules stay in `follow_imports = "silent"` scope until Phase 8. Do not remove existing `# type: ignore` unless the task says so.
- **All new code must have Google-style docstrings** where ruff's `D` rules apply.
- **Migrations are additive.** Never rewrite history in `migrations/`. If a task requires a data migration, add a new numbered file.
- **PostgreSQL and SQLite only.** No MSSQL, no dash, no `mssql-django`. `settings.DATABASE_ENGINE` accepts only `"sqlite"` or `"postgresql"`.
- **URL conventions** per FR‑49: hyphenated, plural, kebab-case where relevant. Rename endpoints as you touch them, not preemptively.
- **Deletion flows** need an intermediate `_confirm_delete.html` (FR‑40) in the UI.

## Testing rules

- Use `pytest` + `pytest-django`. Fixtures in `tests/conftest.py` per app.
- Use `factory_boy` for object creation. Do not use `.objects.create(...)` in tests except when the factory doesn't exist yet.
- Any new code path in your task's `Do` must be covered by tests such that overall coverage stays ≥ 80% and diff coverage on the PR is ≥ 80%.
- Tests for permission-guarded endpoints must exercise the deny path, not just the allow path.

## Ruff / mypy / commit hygiene

- Prefer the ruff autofix pass (`ruff check --fix .`, then `ruff format .`) before opening a PR.
- Do not add broad `# noqa` or `# type: ignore` without a comment naming the phase/task that will remove it (`# TODO(P8): …`).
- Commits are small, self-contained, and each one leaves CI green if you were to stop there.

## What to do when you're blocked

- If your task refers to a task that hasn't landed yet (e.g., P4 references P3 viewsets), open the PR anyway and note the dependency at the top. Do NOT do the missing task yourself.
- If the plan is ambiguous or contradicts the requirements, stop and comment on the issue with the specific conflict; don't guess.
- If a step requires touching Kubernetes / DNS / secrets on the cluster, stop — those changes are manual (see Phase 9).
