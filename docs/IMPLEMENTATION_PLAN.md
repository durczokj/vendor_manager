# Vendor Manager — Refactor Implementation Plan

**Purpose.** This document breaks the refactor mandated by [docs/REQUIREMENTS.md](REQUIREMENTS.md) into concrete, executable phases and tasks that can be handed to coding agents. It is the operational counterpart to the requirements document.

**How to use this document (for agents).**

1. Read [docs/REQUIREMENTS.md](REQUIREMENTS.md) and [docs/ERD.md](ERD.md) first. Every task references specific `FR‑*` / `NFR‑*` items; those are the source of truth for behavior. If a task appears to conflict with a requirement, the requirement wins — surface the conflict, do not paper over it.
2. Work phase by phase. Do not start `P<N+1>` until `P<N>` meets its "Definition of done".
3. Within a phase, tasks tagged `[serial]` MUST be executed in order and by a single agent. Tasks tagged `[parallel-safe]` may be picked up concurrently by different agents. Tasks tagged `[per-app]` are naturally parallel across the seven Django apps (`companies`, `contracts`, `people`, `orders`, `undertakings`, `engagements`, `leaves`).
4. Every task has explicit **acceptance criteria**. A task is not "done" until every criterion holds and the CI pipeline (once it exists, from Phase 0) is green for the introduced changes.
5. Prefer small, reviewable commits. Never mix a mechanical refactor with a behavior change in one commit.
6. If a task is blocked, do not brute-force around it — record the blocker at the bottom of this file under an "Open issues during execution" section and move to the next parallel-safe task.

**Guardrails for every task.**

- **Do not modify the ERD** (per requirements §2.1). Model changes are limited to (i) reconciling contradictions already listed in the requirements' Redundancy Inventory, (ii) adding managers / methods / meta options / services, and (iii) migration squashing.
- **Do not introduce new business logic** that isn't already in the requirements. This is a restructuring refactor, not a feature build.
- **Do not weaken any existing invariant.** Every model-level validation currently enforced (see `FR‑12` through `FR‑17`) MUST remain enforced somewhere (model `clean()`, service, or DB constraint) after the move.
- **Every new module MUST land with type hints** consistent with `mypy --strict` (`NFR‑30`). See Phase 0 for the mypy scope escalation strategy.
- **Every new module MUST land with tests** consistent with the diff-coverage gate (`NFR‑17`).

**Traceability.** Task IDs use `P<phase>.T<n>` (e.g. `P2.T3`). Each task lists the requirements it satisfies. The final acceptance sweep (Phase 9) verifies every `FR‑*` and `NFR‑*` against at least one task ID.

---

## Phase overview

| # | Phase | Goal | Blocking dependencies |
|---|---|---|---|
| P0 | Foundation & tooling | Lint, format, type, CI, secrets, dead code removal. No behavior change. | — |
| P1 | Model cleanup & migration squash | Reconcile contradictions; squash rename-cycle migrations to a linear history. | P0 |
| P2 | Services, selectors, managers | Extract business logic out of models & views into `services.py` / `selectors.py` / `managers.py`. | P1 |
| P3 | REST API surface | Explicit serializers, viewsets, HTTP Basic auth, `/api/v1/`, OpenAPI schema. | P2 |
| P4 | UI consolidation | One `base.html`, one `_list.html`, one `_detail.html`, one `_form.html`, one delete-confirm template; crispy-forms + django-tables2; nav registry. | P3 (per app) |
| P5 | Dashboard rework | Remove `django-plotly-dash`; new JSON endpoint + Plotly.js template; enforce `accessible_to(user)`. | P2, P3 |
| P6 | Documentation site | MkDocs at `/docs/` with three top-level sections — User Guide, Developer Guide, API Reference (Swagger embedded at `/docs/api/`). | P3 |
| P7 | Test hardening | Factories, model/service/API/permission suites, diff-coverage gate live. | Runs alongside P1–P6; final push here. |
| P8 | Strict-typing sweep | Everything that isn't already annotated gets annotated; `mypy --strict` passes on the whole project. | P1–P6 |
| P9 | Acceptance & release | Every `FR‑*` / `NFR‑*` mapped to a passing test; `check --deploy` clean; MkDocs green; k3s deploy verified. | P0–P8 |

---

## Phase 0 — Foundation & tooling

**Goal.** Get the machinery in place so every subsequent phase runs against a green CI pipeline. **No functional behavior changes to the app.** Nothing in this phase requires a database migration.

**Definition of done.**

- `pyproject.toml` is the single source of truth for Ruff, mypy, pytest, coverage, and package metadata.
- `.github/workflows/ci.yaml` runs on every PR and every push to `main` and passes for the code as it is at the end of P0.
- `.github/workflows/deploy.yaml` continues to work for releases (unchanged in shape from what's on `main` today; see `NFR‑24a`).
- Pre-commit runs the same lint + format tools as CI.
- No `print()`, no hand-rolled JSON login view, no MSSQL settings branch, no `docker-compose.prod.yml` in the tree.
- `python manage.py check --deploy` under the production settings profile is either clean or has a documented, tracked list of remaining warnings (they'll be closed by P9).

### P0.T1 — Consolidate tooling into `pyproject.toml` [serial]

**Satisfies.** `NFR‑29`, `NFR‑30`, `NFR‑32`.

**Do.**

- Create/update `pyproject.toml` with sections for `[tool.ruff]`, `[tool.ruff.format]`, `[tool.ruff.lint]`, `[tool.mypy]`, `[tool.django-stubs]`, `[tool.pytest.ini_options]`, `[tool.coverage.run]`, `[tool.coverage.report]`.
- Ruff config: line length 120 (matches current pre-commit), targeted rule set (at minimum `E`, `F`, `W`, `I`, `UP`, `B`, `SIM`, `DJ`, `PT`). Enable `ruff format` as the formatter.
- Remove `black`, `isort` from any dev requirements, `pyproject.toml`, and pre-commit.
- Split runtime vs dev dependencies. Recommendation: `requirements.txt` (runtime, pinned) and `requirements-dev.txt` (dev extras: `ruff`, `mypy`, `django-stubs[compatible-mypy]`, `djangorestframework-stubs[compatible-mypy]`, `pytest`, `pytest-django`, `pytest-cov`, `diff-cover`, `factory_boy`, `mkdocs`, `mkdocs-material`). The existing `requirements-devel.txt` file should be renamed to `requirements-dev.txt` for consistency, or kept if renaming is scoped-creep — pick one and be consistent.

**Acceptance.**

- `ruff check .` and `ruff format --check .` both run and produce a finite (possibly non-zero) error list. The goal here is *the tools work*, not *zero errors*.
- `mypy --version` works with the stubs installed.
- No `black` or `isort` string appears anywhere in the repo (`grep -R 'black\|isort' .` returns only unrelated or historical hits).

### P0.T2 — Rewrite `.pre-commit-config.yaml` [serial]

**Satisfies.** `NFR‑29`, `NFR‑32`.

**Do.**

- Replace `black` and `isort` hooks with `ruff` (both `ruff` and `ruff-format`).
- Keep the generic hooks (`trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-json`, `detect-private-key`, `check-added-large-files`).
- Add a `django-upgrade` hook targeting the project's Django version.
- Add a `manage.py check --deploy` hook that runs against the production settings profile (may be a local hook running `python manage.py check --deploy`).
- Do NOT add mypy to pre-commit (too slow); it runs in CI.
- Update the `default_language_version.python` from `python3.9` to the actual production Python.

**Acceptance.**

- `pre-commit run --all-files` executes without errors on a clean checkout after P0 completes.
- The hooks match, one-for-one, the fast tools listed in `NFR‑32`.

### P0.T3 — Author `.github/workflows/ci.yaml` [serial]

**Satisfies.** `NFR‑31`.

**Do.**

- Create `.github/workflows/ci.yaml`. Triggers: `pull_request`, `push` to `main`.
- Steps, in order (all MUST run; individual failures MUST fail the workflow):
  1. Check out, set up Python (match `Dockerfile`).
  2. Install `requirements.txt` + `requirements-dev.txt`.
  3. `ruff check .`
  4. `ruff format --check .`
  5. `mypy` (see P0.T4 for scope escalation)
  6. `pytest --cov=. --cov-report=xml`
  7. `diff-cover coverage.xml --compare-branch=origin/main --fail-under=80` (skipped on `push: main`, active on PRs)
  8. Overall coverage threshold: `coverage report --fail-under=80`
  9. `DJANGO_SETTINGS_MODULE=vendor_manager.settings python manage.py check --deploy` under a production-like env
  10. `mkdocs build --strict` (see Phase 6; before Phase 6 this step MAY be a no-op that prints "MkDocs not yet configured" and exits 0 — but flip it to enforcing before P6 lands)
- Concurrency: cancel in-progress runs for the same PR.

**Acceptance.**

- CI runs green on the P0 finishing commit.
- CI is red if any step fails.

### P0.T4 — Introduce `mypy --strict` scope, escalating [serial]

**Satisfies.** `NFR‑30`.

**Do.**

- Initial `mypy` config: `strict = true`, `plugins = ["mypy_django_plugin.main", "mypy_drf_plugin.main"]`, `[tool.django-stubs] django_settings_module = "vendor_manager.settings"`.
- Exclude, initially: `migrations/`, `staticfiles/`, `manage.py`, `**/tests.py` (they will be re-included in P7/P8), `dashboards/summary_dashboard.py` (going away in P5).
- Set the `files` or `packages` list to *only the modules edited or created in P0*. This means Phase 0 does NOT annotate the whole codebase; it locks the *bar* at strict for new/changed code and defers the sweep to P8.
- Add a `# type: ignore[…]` inventory file (`docs/mypy-baseline.md` or similar) is NOT permitted — do not introduce a stale-baseline tool. If a legitimate escape hatch is needed, use a precise `# type: ignore[error-code]` on that specific line with a `# TODO(P8): …` comment referencing the module to be annotated.

**Acceptance.**

- `mypy` runs in CI and passes for the P0 scope.
- Adding a deliberately mistyped function to a P0-scope module fails CI.

### P0.T5 — Fix settings and secrets [parallel-safe]

**Satisfies.** `NFR‑12`, `NFR‑13`, `NFR‑14`, `NFR‑15`, `NFR‑23`, `NFR‑28`.

**Do.**

- In `vendor_manager/settings.py`:
  - `DEBUG` MUST default to `False` when the env var is unset or empty. The current pattern (`DEBUG = os.environ.get("DEBUG", "")`) is truthy — replace with an explicit `env_bool` helper.
  - `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` MUST come from env (comma-split), with sensible dev defaults gated on `DEBUG`.
  - `SECRET_KEY` MUST come from env with no in-repo default. Fail loudly at startup if unset in a non-dev context.
  - Remove the MSSQL settings branch entirely. Only support PostgreSQL (via `DATABASE_*` env vars) and SQLite (via a `DATABASE_URL=sqlite:///…` or `DATABASE_ENGINE=django.db.backends.sqlite3` selector). Choose one env-shape and document it in Phase 6.
- Remove `mssql-django` (or equivalent MSSQL driver) from `requirements.txt`.

**Acceptance.**

- `python manage.py check --deploy` under the production settings profile emits no `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, or `SESSION_COOKIE_SECURE` warnings.
- `grep -R 'mssql\|pyodbc' .` returns no application-code hits.
- Boot with `DEBUG=` (empty string) results in `settings.DEBUG is False`.

### P0.T6 — Delete `docker-compose.prod.yml` and clean compose docs [serial]

**Satisfies.** `NFR‑24`.

**Do.**

- `git rm docker-compose.prod.yml`.
- Verify nothing references it (`grep -R 'docker-compose.prod' .` returns only historical hits in the change log).
- Add a short `README.md` section (temporary until Phase 6) explaining the two dev modes: (i) `docker compose up` for DB + `python manage.py runserver` for app, (ii) pure SQLite via env var.

**Acceptance.**

- The file is gone.
- CI still passes.
- CD workflow (`.github/workflows/deploy.yaml`) is untouched by this task — it already targets k3s per `NFR‑24a`.

### P0.T7 — Remove hand-rolled `login_api` and the `print()` decorator [serial]

**Satisfies.** `NFR‑10`, `NFR‑27`, `NFR‑28`, redundancy-inventory entries.

**Do.**

- Delete the `login_api` view and the `print(f"Permission: {permission_name}")` decorator from `vendor_manager/views.py`.
- Delete the corresponding URL entry.
- If any current test / client uses `login_api`, redirect them to Django's `LoginView` / DRF Basic auth (details land in P3, but the removal must happen now so no dead code remains).
- Replace any remaining `print(…)` in application code with `logging.getLogger(__name__).…()` calls at the appropriate level.

**Acceptance.**

- `grep -R "print(" .` returns zero application-code hits.
- `grep -R "csrf_exempt\|login_api" .` returns zero hits outside historical migration files and this document.

### P0.T8 — Structured stdout logging [parallel-safe]

**Satisfies.** `NFR‑27`, `NFR‑36`, `NFR‑37`.

**Do.**

- Add a `LOGGING` config in `settings.py` that writes to stdout in JSON (recommended: `python-json-logger`) or logfmt.
- Include a logging middleware or a filter that adds `user_id` to the log record for authenticated requests.
- Ensure Django's default `django.request` and `django.security` loggers propagate to the new handler at appropriate levels.
- Unhandled exceptions log at `ERROR` with traceback. Django's `AdminEmailHandler` MUST NOT be enabled.

**Acceptance.**

- `python manage.py runserver` emits JSON/logfmt lines to stdout, not plain text.
- A deliberately triggered 500 emits an `ERROR` line with a traceback field.

---

## Phase 1 — Model cleanup & migration squash

**Goal.** Reconcile the small model contradictions listed in the Redundancy Inventory and collapse rename-cycle migration history to a single, forward-only initial per app.

**Definition of done.**

- Every model contradiction listed here is fixed.
- Each of the seven apps has migration history that starts from `0001_initial` (or a squashed initial) and moves forward monotonically. No `RenameField` cycles remain.
- `python manage.py migrate --plan` produces a linear plan.
- No behavior change is observable in the UI or API.

### P1.T1 — Reconcile `Person` field nullability and add `Contract.__str__` [serial]

**Satisfies.** Redundancy Inventory items 12 & 13.

**Do.**

- `Person.description` (currently `TextField(blank=False, null=True)`): pick and apply the intended semantics. Since the ERD types are immutable but the ERD does not dictate `blank`/`null`, the correct fix is `TextField(blank=True, null=False, default="")`. Same for `Person.location` → `CharField(max_length=255, blank=True, null=False, default="")`. Generate a data migration that maps existing `NULL` values to `""`.
- Add `Contract.__str__` returning `self.name`.
- Fix the double-docstring in `Person.get_assignments` and the typo `assignmnents`.

**Acceptance.**

- `pytest` (with the new invariant tests scheduled in P7 stubbed as `xfail` if not yet ready) still passes.
- `python manage.py makemigrations --dry-run` after the changes reports "No changes detected".

### P1.T2 — Squash migrations per app [per-app, but serial within an app]

**Satisfies.** `NFR‑20`, `NFR‑22`.

**Do (for each of `companies`, `contracts`, `people`, `undertakings`, `orders`, `engagements`, `leaves`).**

- Run `python manage.py squashmigrations <app> 0001 <latest>` to produce a squashed initial. Review the output to ensure it captures the current state.
- Delete the pre-squash migration files (only after CI on the squashed migration passes on both SQLite and PostgreSQL).
- For `engagements`, note that a squashed `0001_initial_squashed_0011_rename_identifier_engagement_id.py` already exists; verify it is authoritative and remove the loose `0001_initial.py` etc. that co-exist alongside it (they should already be superseded).
- Every squashed migration MUST have a proper `dependencies` list and MUST NOT contain any `RunPython` operation without a `reverse_code` — if one is needed, document it inline.

**Acceptance.**

- `python manage.py migrate` from an empty DB succeeds on SQLite and PostgreSQL.
- `python manage.py migrate --plan` shows exactly one `0001_initial` (or `0001_initial_squashed_*`) per app plus any deliberate post-squash follow-ups.
- `grep -R "identifier" **/migrations/` returns no hits (no residue of the rename cycle).
- Applying the squashed migrations against a database populated from the *old* migration history results in `django-admin migrate` marking them applied without altering any rows (Django's replaced-migrations mechanism).

### P1.T3 — Add `<Entity>QuerySet` skeletons [per-app, parallel-safe]

**Satisfies.** `NFR‑7`, `FR‑28`.

**Do.**

- For every entity in `FR‑1` through `FR‑11`, create a `managers.py` file in its app with a `<Entity>QuerySet(models.QuerySet)` class and a `<Entity>Manager = <Entity>QuerySet.as_manager()`-style manager.
- Wire the manager on the model via `objects = <Entity>Manager()`.
- Add a stub method `accessible_to(self, user) -> "<Entity>QuerySet": raise NotImplementedError` on each queryset. The actual implementation lands in P2.T5 once the canonical permission names are settled.

**Acceptance.**

- Every model has `.objects` typed as `<Entity>QuerySet` (verifiable by `Model.objects.all()` returning a `<Entity>QuerySet` instance in a shell).
- `mypy` passes on the new files (they must be in-scope per P0.T4 escalation).

---

## Phase 2 — Services, selectors, managers

**Goal.** Extract every non-trivial write operation into `services.py`, every non-trivial read/query into `selectors.py`, and every custom queryset method into `managers.py`. After this phase, models are thin (structure + invariants), views are thin (orchestration), and both UI and API can call the same layer.

**Definition of done.**

- `Order.create_new_version` lives in `orders/services.py` and is transactional.
- `Engagement.costs` and `Engagement.cost_coverage` live in `engagements/selectors.py`.
- Every entity has an `accessible_to(user)` queryset method implemented (not stubbed).
- No business logic remains in `views.py` for any app.
- The permission name inconsistencies in `vendor_manager/roles.py` are reconciled to a single canonical set.

### P2.T1 — Extract `Order.create_new_version` to `orders/services.py` [serial]

**Satisfies.** `FR‑18`, `NFR‑1`, `NFR‑2`.

**Do.**

- Create `orders/services.py` with `create_new_order_version(*, order: Order, contract: Contract, start_date: date, end_date: date, copy_engagement_assignments: bool = True) -> OrderVersion` wrapped in `transaction.atomic()`.
- Move the current `Order.create_new_version` body verbatim into the service, then delete the model method (or keep a thin `@classmethod` wrapper that forwards to the service, deprecated with a comment — pick "wrapper" if any existing code path calls it; otherwise delete outright).
- Fix the subtle bug where the current implementation shortens the previous version but does NOT re-run `OrderVersion.clean()` on it (so it silently violates `FR‑16`'s no-gap rule under some edge cases). The service MUST call `.full_clean()` on the mutated previous version and the new version before saving.

**Acceptance.**

- New test in `orders/tests/test_services.py` covers: happy path, contract already used (raises `IntegrityError`), start_date <= previous version's start_date (raises `ValidationError`), rollback on failure of assignment copy.
- All existing tests still pass.

### P2.T2 — Extract cost calculations to `engagements/selectors.py` [serial]

**Satisfies.** `FR‑19`, `NFR‑1`, `NFR‑2`, `NFR‑8`.

**Do.**

- Create `engagements/selectors.py` with two functions: `engagement_costs(engagement: Engagement) -> list[dict]` and `engagement_cost_coverage(engagement: Engagement) -> list[dict]`.
- Move the bodies of `Engagement.costs` and `Engagement.cost_coverage` into these selectors. Replace `self` with an explicit `engagement` parameter.
- The current model properties MUST become thin wrappers that call the selectors, or be deleted outright. Prefer *deleting* the properties and updating all call sites to use the selectors — properties on the model tempt future authors to add more logic back.
- Wrap the DB access in `select_related` / `prefetch_related` at the selector boundary so the callers get single-query semantics.
- Replace the `raise Exception("Total coverage …")` with a `ValidationError` subclass or a dedicated `CoverageOverAllocationError` — never bare `Exception`.
- Replace `logging.warning(…)` on under-allocation with a properly-configured logger call using the module logger.

**Acceptance.**

- New tests in `engagements/tests/test_selectors.py` verify the exact numeric output for a fixture-based scenario (used as the baseline for acceptance criterion 9).
- The dashboard (still Dash at this point) continues to render identically.
- `Engagement.costs` and `Engagement.cost_coverage` as attributes no longer exist on the model (or are one-line delegating properties, if you kept them).

### P2.T3 — Extract remaining model behavior into services [per-app, parallel-safe]

**Satisfies.** `NFR‑1`, `NFR‑2`, `FR‑12`–`FR‑17`.

**Do.**

- For each app, review every `save()` / `clean()` / property with side effects. Anything that is a multi-step business rule or spans models moves to `services.py`. Simple invariants (single-field range checks, single-model uniqueness) stay in `clean()`.
- Specifically:
  - `Engagement.save`'s "adjust child assignment dates" behavior (implements `FR‑15`) moves to `engagements/services.py::update_engagement(...)`. The model `save()` remains simple.
  - `EngagementOrderVersionAssignment.clean` (implements `FR‑13`) stays on the model.
  - `EngagementUndertakingAssignment.clean` (implements `FR‑14`) stays on the model.
  - `OrderVersion.clean` (implements `FR‑16`) stays on the model but MUST be called by every service that mutates it.

**Acceptance.**

- `views.py` files across all apps import from `<app>/services.py` and `<app>/selectors.py`; they do not construct model instances directly for anything more complex than the trivial create/update path (that path stays via `ModelForm.save()`).
- Every model invariant test from `FR‑12`–`FR‑17` (added in P7) passes against both the model layer and the service layer.

### P2.T4 — Reconcile permission names [serial]

**Satisfies.** `FR‑25`.

**Do.**

- Read `vendor_manager/roles.py`. Identify every naming inconsistency (`view_engagement_undertaking_version_assignment` vs `..._undertaking_assignment` etc.).
- Adopt one canonical set: `{view,add,change,delete}_<snake_case_model_name>` where `<snake_case_model_name>` is Django's default (`engagement_undertaking_assignment`, `engagement_order_version_assignment`, `cost_center`, etc.).
- Update every permission reference across `permissions.py` files, decorators, and the roles registry.
- Add a data migration that renames any stored `Permission` rows using the old codenames to the new codenames, so existing production databases don't lose permission grants.

**Acceptance.**

- `grep -R "view_engagement_undertaking_version" .` returns zero hits.
- Every role in `vendor_manager/roles.py` compiles at startup (no `KeyError` for unknown permission).
- A test verifies that each of the three roles (`Person`, `UndertakingManager`, `Admin`) has the expected permission set.

### P2.T5 — Implement `<Entity>QuerySet.accessible_to(user)` [per-app, parallel-safe]

**Satisfies.** `FR‑26`, `FR‑27`, `FR‑28`, `NFR‑7`.

**Do.**

- For each entity, implement `accessible_to(user)` as a queryset method that returns the ORM-filtered subset the user may view. This MUST be the *single source of truth* for object-level access — the current per-entity `access_<entity>` object-level checkers become thin wrappers that check membership of the entity in `type(entity).objects.accessible_to(user)`.
- The three roles' semantics (from `vendor_manager/roles.py`):
  - `Admin`: `accessible_to(user).return self` — full access.
  - `UndertakingManager`: access to `Undertaking`s they manage and everything reachable from those (engagements assigned to their undertakings, the people of those engagements, the orders/versions supporting them, etc. — exact scope MUST match today's per-entity `access_*` logic).
  - `Person`: access to their own `Person`, their `Engagement`s, their `Leave`s, and the entities read-through-those.
- Reject the temptation to iterate in Python: every `accessible_to` MUST be pure ORM (`.filter(…)`, subqueries, `Exists()`), no `.all()` + list comprehension.

**Acceptance.**

- A permission-matrix test (P7.T5) confirms that for each of the three roles, `list(Entity.objects.accessible_to(user))` matches the enumeration produced by calling `access_<entity>(user, e)` for every `e in Entity.objects.all()`.
- Query count for `Entity.objects.accessible_to(user)` is a *constant* (independent of DB size) as measured by `django.test.utils.CaptureQueriesContext`.

---

## Phase 3 — REST API surface

**Goal.** Every entity is exposed via a DRF `ModelViewSet` under `/api/v1/`, using explicit serializers and shared services. HTTP Basic auth works end-to-end. OpenAPI schema is published.

**Definition of done.**

- `POST /api/v1/…`, `GET /api/v1/…`, `PATCH`, `DELETE` work for every entity in `FR‑1` through `FR‑11`.
- All four custom actions in `FR‑31` exist and behave.
- `curl -u user:pass https://…/api/v1/companies/` works.
- OpenAPI schema at `/api/v1/schema/`; Swagger UI at `/docs/api/`.
- The hand-rolled `login_api` is fully replaced.
- `scripts/populate.py` builds the full sample dataset end-to-end via the API against a running local instance (see P3.T6). The legacy `notebooks/populate.py` is gone.

### P3.T1 — Global DRF config [serial]

**Satisfies.** `FR‑22`, `FR‑29`, `FR‑32`, `FR‑33`, `FR‑34`, `NFR‑10`.

**Do.**

- In `settings.py`, configure `REST_FRAMEWORK`:
  - `DEFAULT_AUTHENTICATION_CLASSES`: `SessionAuthentication`, `BasicAuthentication` (in that order).
  - `DEFAULT_PERMISSION_CLASSES`: `IsAuthenticated`.
  - `DEFAULT_PAGINATION_CLASS`: `PageNumberPagination` with `PAGE_SIZE = 50`, `MAX_PAGE_SIZE = 200`.
  - `DEFAULT_FILTER_BACKENDS`: `DjangoFilterBackend`, `SearchFilter`, `OrderingFilter`.
  - `DEFAULT_SCHEMA_CLASS`: `drf_spectacular.openapi.AutoSchema`.
  - `EXCEPTION_HANDLER`: leave default; ensure `ValidationError` from model `clean()` surfaces as HTTP 400 with DRF's error shape (custom handler if needed — do NOT invent a new error format).
- Add `django-filter` and `drf-spectacular` to `requirements.txt`.
- Add `rest_framework`, `django_filters`, `drf_spectacular` to `INSTALLED_APPS`.
- Create `/api/v1/` URL namespace in `vendor_manager/urls.py` and mount `include("api.urls")` (see P3.T2 for router structure).
- Add `SPECTACULAR_SETTINGS` block: title, description, version (from a single source), servers list from env.

**Acceptance.**

- `curl -u <staff>:<pw> http://localhost:8000/api/v1/schema/` returns valid OpenAPI JSON.
- Anonymous request to `/api/v1/companies/` returns 401 (with `WWW-Authenticate: Basic` header).
- Session-authed request to `POST /api/v1/companies/` without CSRF token returns 403 (session auth requires CSRF).
- Basic-authed request to `POST /api/v1/companies/` without CSRF token returns 201 (Basic auth is CSRF-exempt).

### P3.T2 — Explicit serializers, viewsets, and routers [per-app, parallel-safe once P3.T1 lands]

**Satisfies.** `FR‑29`, `FR‑30`, `FR‑34`, `NFR‑4`.

**Do (for each of the eleven entities).**

- Create `<app>/serializers.py` with a `<Entity>Serializer(serializers.ModelSerializer)`. Every field MUST be listed explicitly (`fields = [...]`). No `fields = "__all__"`. Related fields render as PK by default; add a nested read-only representation only where the UI needs it in the same round-trip.
- Create `<app>/api.py` with a `<Entity>ViewSet(viewsets.ModelViewSet)`:
  - `queryset = Entity.objects.all()`
  - `serializer_class = <Entity>Serializer`
  - `filterset_class = <Entity>FilterSet` (in `<app>/filters.py`)
  - `search_fields = [...]` (human-readable fields)
  - `ordering_fields = [...]`
  - Override `get_queryset` to `return super().get_queryset().accessible_to(self.request.user)` (enforces `FR‑27`, `FR‑28`).
  - `perform_create` / `perform_update` MUST call into `<app>/services.py` when the operation is not a trivial `serializer.save()` (e.g. engagement update triggers assignment date adjustments — this is `FR‑15`).
- Create `<app>/urls.py` API section that registers the viewset on a DRF `DefaultRouter`. Include it from `api/urls.py` under `/api/v1/`.
- URL naming: DRF's default `<basename>-list` / `<basename>-detail` MUST match `FR‑50`. Set `basename` explicitly if the default doesn't match.

**Acceptance.**

- All CRUD verbs work for every entity with both Basic and session auth.
- Every list endpoint respects `accessible_to(user)`.
- OpenAPI schema lists every viewset with a description generated from docstrings.

### P3.T3 — Nested + flat assignment endpoints [serial]

**Satisfies.** `FR‑49`, redundancy-inventory item on duplicate assignment URL files.

**Do.**

- Add `drf-nested-routers` to `requirements.txt`.
- Under `/api/v1/engagements/<pk>/undertaking-assignments/` (nested router): full CRUD for `EngagementUndertakingAssignment` scoped to the engagement.
- Under `/api/v1/engagements/<pk>/order-version-assignments/` (nested router): full CRUD for `EngagementOrderVersionAssignment` scoped to the engagement.
- Also expose flat, filterable endpoints for reporting: `/api/v1/engagement-undertaking-assignments/?engagement=<id>` and `/api/v1/engagement-order-version-assignments/?engagement=<id>`.
- Delete the two separate URL files (`engagement_order_version_assignment_urls.py`, `engagement_undertaking_assignment_urls.py`) that currently exist in `engagements/`. Everything routes through the single nested + flat scheme above.

**Acceptance.**

- OpenAPI schema shows both nested and flat endpoints, correctly parameterized.
- Both routes reach the same viewset code path via the router.
- The two deleted URL files no longer exist and no `include(…)` references them.

### P3.T4 — Custom `@action` endpoints [serial after P3.T2]

**Satisfies.** `FR‑31`.

**Do.**

- `POST /api/v1/orders/{id}/versions/clone-latest/` — a viewset action on `OrderViewSet` that calls `orders.services.create_new_order_version(...)`. Request body: `{contract_id, start_date, end_date, copy_engagement_assignments=true}`.
- `GET /api/v1/engagements/{id}/costs/` — returns `engagements.selectors.engagement_costs(engagement)`.
- `GET /api/v1/engagements/{id}/cost-coverage/` — returns `engagements.selectors.engagement_cost_coverage(engagement)`.
- `GET /api/v1/people/{id}/assignments/` — returns the person's undertaking assignments, filtered by `EngagementUndertakingAssignment.objects.accessible_to(request.user)`.

**Acceptance.**

- Every custom action is documented in the OpenAPI schema (via `@extend_schema` where necessary).
- Object-level access is enforced (a `Person`-role user cannot clone a version of an order they can't access).

### P3.T5 — Auth glue and `/health/` [serial]

**Satisfies.** `FR‑21`, `FR‑22`, `FR‑23`, `NFR‑11`, `NFR‑39`.

**Do.**

- `/accounts/login/` and `/accounts/logout/` served by Django's built-in `LoginView` / `LogoutView`. Template: a single minimal `registration/login.html` (crispy-forms once P4 lands; plain HTML acceptable for now).
- Add a middleware or a `LoginView` subclass that blocks users without a linked `Person` at UI login and returns a readable error. In the API, add a DRF permission `HasLinkedPerson` composed with `IsAuthenticated` on every viewset (via `DEFAULT_PERMISSION_CLASSES`), returning 403 with the message from `FR‑23`.
- `/health/` view: unauthenticated, returns 200 with body `OK` (or `{"status": "ok"}`) and touches the DB with `connection.cursor()` to prove connectivity. Registered at the *root* URL conf, not under `/api/v1/`, so k3s probes hit the same path regardless of API versioning.
- `/api/v1/schema/` and `/docs/api/` MUST require authentication in prod. Serve them via `drf-spectacular`'s `SpectacularAPIView` / `SpectacularSwaggerView` with `permission_classes=[IsAuthenticated]`.

**Acceptance.**

- Logging in via `/accounts/login/` and then hitting `/api/v1/companies/` in the same browser session works with no explicit token.
- `curl -u user:pass http://.../api/v1/companies/` works.
- `curl http://.../health/` returns 200 with no auth.
- A user whose `Person` was deleted receives 403 with the correct error message on any API call.

### P3.T6 — API-based sample data / smoke script [serial]

**Satisfies.** `FR‑29`–`FR‑35`, `NFR‑16` (dual-use: fixture builder for local dev + end-to-end API smoke test).

**Context.** The current `notebooks/populate.py` populates the DB via direct ORM access (`Model.objects.all().delete()`, `instance.save()`, `Order.create_new_version(...)`). That script has served as the local "make me a realistic dataset" helper. It MUST be replaced with an API-only version that exercises every endpoint the app exposes, so that (a) a fresh developer can prime a local DB with one command, and (b) the same script doubles as an end-to-end smoke test that proves the API is functional against a running instance (dev, staging, or a post-deploy k3s check).

**Do.**

- Create `scripts/populate.py` (top-level `scripts/` directory; not inside `notebooks/` since it is no longer a notebook helper).
- The script MUST:
  - Take CLI args: `--base-url` (default `http://localhost:8000`), `--user`, `--password`, `--reset` (optional, see below), `--seed` (optional integer for deterministic runs).
  - Use `requests` (add to `requirements-dev.txt`, not runtime) with HTTP Basic auth. No cookies, no CSRF handling required.
  - Create the same shape of dataset as the current `notebooks/populate.py`: 2 `CostCenter`s, 6 `Undertaking`s + 6 manager `Person`s, 3 `Company`s, 3 `Order`s + 3 `Contract`s + 3 initial `OrderVersion`s, 30 consultant `Person`s with `Engagement`s and assignments, 3 `Leave`s, and 2 order-version clones exercising `POST /api/v1/orders/{id}/versions/clone-latest/`.
  - Every write goes through `/api/v1/…` endpoints — no Django imports, no ORM, no `django.setup()`. The script is a standalone CLI that could be run from any machine with network reach to the app.
  - Use deterministic seeded randomness (`random.seed(args.seed)`, `Faker(args.seed)`) so re-runs with the same seed produce identical results — this is what makes it a smoke test rather than a chaos monkey.
  - Fail loudly on any non-2xx response, printing the endpoint, request body, and response body. Every HTTP call MUST be wrapped in a small helper that raises on error.
  - Report a one-line summary at the end: counts created per entity + wall-clock time.
- `--reset` behavior: if passed, the script FIRST deletes every entity it will re-create. Since deletion via the API is order-sensitive (assignments before engagements before people, etc.), the script MUST walk the entities in reverse dependency order: assignments → leaves → engagements → order versions → orders → contracts → people (non-manager) → undertakings → cost centers → companies → managers. If any DELETE fails with 4xx due to residual references, print the offender and abort — do not silently continue.
- The script MUST NOT require Django `SECRET_KEY`, `DATABASE_URL`, or any env var beyond what `requests` needs. It is a pure HTTP client.
- The old `notebooks/populate.py` MUST be deleted in the same commit.
- Add a section to `docs/local-dev.md` (see P6.T1) documenting the invocation:

  ```
  python scripts/populate.py --base-url http://localhost:8000 --user admin --password admin --reset --seed 42
  ```

- Add a companion `scripts/populate.md` (or fold into `docs/local-dev.md`) that lists what the script creates and what endpoints it exercises, so a reader can quickly see the coverage without reading the script.

**Optional (recommended but not required).**

- Add a `pytest` end-to-end test that runs `scripts/populate.py --base-url http://testserver …` against a `LiveServerTestCase` and asserts the summary counts. This makes the script part of the CI smoke net without a separate integration environment.
- Add a `smoke:` step to `.github/workflows/deploy.yaml` (post-deploy on a `workflow_dispatch` or a staging environment) that invokes the script against the freshly deployed URL to prove the release is functional.

**Acceptance.**

- Running `python scripts/populate.py --base-url http://localhost:8000 --user <admin> --password <pw> --reset --seed 42` against a freshly-migrated dev DB completes without errors and produces exactly the same entity counts as the current `notebooks/populate.py` (2 CCs, 6 Undertakings, 3 Companies, 3 Orders, at least 4 Contracts and OrderVersions accounting for the two clones, 36 Persons total, 30 Engagements, ≥30 undertaking assignments, 3 Leaves).
- Re-running with the same seed after the DB has been re-migrated produces identical primary-key values (for entities with business-assigned PKs) and identical string fields — the script is deterministic.
- Running WITHOUT `--reset` against a DB that already has data results in 4xx errors on unique-constraint conflicts, and the script exits non-zero with a clear message. It does not partially populate.
- Every endpoint the app exposes for the covered entities is exercised at least once (list, create, and — for orders — the `clone-latest` custom action). Endpoints for entities not covered by the sample dataset (there should be none in scope) are called out in the script's docstring.
- `grep -R "django.setup\|from .*.models import" scripts/populate.py` returns zero hits.
- `notebooks/populate.py` no longer exists.

---

## Phase 4 — UI consolidation

**Goal.** Collapse the seven copies of `add_X.html`, `edit_X.html`, `all_X.html`, `X_details.html` into a single shared set of generic templates. Every entity screen is a declaration ("show these columns", "show these related blocks"), not a re-implementation.

**Definition of done.**

- Exactly one `base.html`, one `_list.html`, one `_detail.html`, one `_form.html`, one `_confirm_delete.html` (or `_delete.html`) exists in `vendor_manager/templates/`.
- All per-entity `add_*.html`, `edit_*.html`, `all_*.html`, `*_details.html` templates are deleted.
- Sidebar navigation is generated from a single registry in `vendor_manager/navigation.py`.
- Delete flows use an intermediate confirmation page.
- No hard-coded `/entity/` URLs; no inline `style=`; no `border="1"`.

### P4.T1 — Shared base template + CSS cleanup [serial]

**Satisfies.** `FR‑37`, `FR‑41`, `FR‑42`, `NFR‑26`, `NFR‑35`.

**Do.**

- Consolidate `master.html` and any near-duplicate base into a single `base.html` in `vendor_manager/templates/`.
- Move all inline `style="…"` and `border="1"` attributes into `staticfiles/table_styles.css` and `staticfiles/styles.css`.
- Replace the fixed 20% / 80% flex layout with a CSS Grid or Flex rule that has `min-width` on both columns and does not overflow on narrow terminals.
- The `messages` block renders once in `base.html`; no template re-renders it.
- Every internal link in `base.html` uses `{% url 'name-of-view' %}`, never a literal `/companies/` etc.

**Acceptance.**

- `grep -R 'style="' vendor_manager/templates/ companies/templates/ …` returns zero hits.
- `grep -R 'border="1"' .` returns zero hits.
- `grep -R 'href="/[a-z]' vendor_manager/templates/` returns zero hits.
- A visual check at 1024px, 768px, and 480px viewport shows no horizontal overflow.

### P4.T2 — Generic CRUD templates + crispy + tables2 [serial]

**Satisfies.** `FR‑37`, `FR‑38`.

**Do.**

- Add `django-crispy-forms` and `crispy-bootstrap5` (or the neutral pack if you prefer no Bootstrap CSS — pick one and be consistent) to `requirements.txt`.
- Add `django-tables2` to `requirements.txt`.
- Create three generic templates in `vendor_manager/templates/`:
  - `_list.html` — receives a `table` (a `django-tables2.Table` instance) and an `add_url`; renders the table with the shared partial and the "Add" button.
  - `_detail.html` — receives an `object`, a list of `fields` (declared per entity), and a list of `related_blocks` (each block is a mini-table with its own `<Related>Table`).
  - `_form.html` — receives a `form` (crispy-rendered) and a `submit_label`; used for both create and edit.
- Delete every per-entity `add_*.html`, `edit_*.html`, `all_*.html`, `*_details.html`.
- Every UI view (Django CBV) declares only *what* to show. The *how* lives entirely in the three templates above.

**Acceptance.**

- `find . -name 'add_*.html' -o -name 'edit_*.html' -o -name 'all_*.html' -o -name '*_details.html'` returns nothing.
- Every entity CRUD screen renders through the three generic templates.
- `grep -c 'extends "master.html"' **/templates/*.html` (or its new equivalent for `base.html`) returns roughly the number of entity screens, not multiples of it (per acceptance criterion 4).

### P4.T3 — Django CBV pass-through to services [per-app, parallel-safe]

**Satisfies.** `FR‑36`, `NFR‑2`, `NFR‑3`.

**Do.**

- Rewrite `views.py` for each app using Django's `ListView`, `DetailView`, `CreateView`, `UpdateView`, `DeleteView` (or a small shared subclass). Every view:
  - Overrides `get_queryset` to call `.accessible_to(self.request.user)`.
  - Calls into `<app>/services.py` for non-trivial writes.
  - Passes a `Table` instance to `_list.html` and a `field spec` to `_detail.html`.
- Delete the current `BaseListView` / `BaseDetailView` closure machinery.
- Delete the `is_api_request()` branching — API and UI now have physically separate view classes.

**Acceptance.**

- `grep -R 'is_api_request' .` returns zero hits.
- Each `views.py` file is <150 lines.
- Every UI view is reachable by a `reverse('<entity>-list')` etc. per `FR‑50`.

### P4.T4 — Sidebar navigation registry [serial]

**Satisfies.** `FR‑39`.

**Do.**

- Create `vendor_manager/navigation.py` with a `NAV_ENTRIES: list[NavEntry]` structure. Each entry: label, URL name, permission required (a callable receiving the user), optional icon.
- Add a `nav` context processor that exposes the filtered nav for the current user.
- `base.html` renders the sidebar by iterating over the context's `nav` list, with zero hard-coded entity links.

**Acceptance.**

- Adding a new entity requires exactly one line added to `NAV_ENTRIES`.
- A `Person`-role user does not see nav entries for entities they cannot access.
- `grep -R 'href="{% url' vendor_manager/templates/base.html` contains the sidebar loop but no per-entity `{% url %}` calls.

### P4.T5 — Intermediate delete confirmation [serial]

**Satisfies.** `FR‑40`.

**Do.**

- Every entity gets a `GET /entity/<id>/delete/` route rendering a single shared `_confirm_delete.html` template that says "Delete <object>? [Yes] [Cancel]".
- Submitting the form (`POST /entity/<id>/delete/`) triggers the delete via the corresponding service.
- Remove all inline `onclick="confirm(…)"` JS in templates. Delete the shared JS helper file if it becomes empty.

**Acceptance.**

- `grep -R 'onclick' vendor_manager/templates/ **/templates/` returns zero hits.
- With JavaScript disabled in the browser, delete still works end-to-end via the confirmation page.

---

## Phase 5 — Dashboard rework

**Goal.** Remove `django-plotly-dash`. Replace it with a JSON endpoint + a minimal Plotly.js template. Access control is enforced through the same `accessible_to(user)` selectors used everywhere else.

**Definition of done.**

- `django-plotly-dash` and `dashboards/summary_dashboard.py` are gone.
- `GET /api/v1/dashboards/summary/` returns pre-aggregated data.
- `/` renders a minimal template that fetches from that endpoint.
- A `Person`-role user cannot see aggregates that include entities they cannot access.

### P5.T1 — Author `dashboards/selectors.py` and `dashboards/services.py` [serial]

**Satisfies.** `FR‑44`, `FR‑45`, `FR‑47`.

**Do.**

- Move all data preparation from `dashboards/summary_dashboard.py` into `dashboards/selectors.py`. Every query MUST start from `<Entity>.objects.accessible_to(user)` — the `user` parameter is passed all the way down.
- `dashboards/services.py::build_summary(user, class_, granularity, date_range, entity_selection) -> SummaryPayload` orchestrates the selectors and returns a serializable payload.
- No pandas / numpy in the selector *signatures* (they may be used internally for aggregation). The selectors return plain Python structures the serializer can render as JSON.

**Acceptance.**

- Unit tests in `dashboards/tests/test_services.py` cover the four filter dimensions and the three roles.
- A `Person`-role user's summary payload for `class_=Person` MUST include *only* their own person (and their related aggregates), never anyone else's, even in totals.

### P5.T2 — `POST/GET /api/v1/dashboards/summary/` endpoint [serial]

**Satisfies.** `FR‑46`, `FR‑47`.

**Do.**

- New DRF viewset or `APIView` at `/api/v1/dashboards/summary/` (mount under a `dashboards/api.py`).
- Accepts the filter params (`class_`, `granularity`, `date_from`, `date_to`, entity selections).
- Delegates to `dashboards.services.build_summary(request.user, …)`.
- Serializer defines the payload shape explicitly; documented via `@extend_schema`.

**Acceptance.**

- OpenAPI schema documents the request/response.
- API tests verify each role's response.

### P5.T3 — Minimal Plotly.js template at `/` [serial]

**Satisfies.** `FR‑43`, `FR‑46`.

**Do.**

- Create `vendor_manager/templates/dashboards/summary.html` extending `base.html`.
- Include Plotly.js from a versioned CDN (or as a vendored asset under `staticfiles/js/`).
- Template loads the summary endpoint via `fetch()` (same-origin, session auth works via the browser cookie), renders one Plotly chart and one table (through `django-tables2` or the shared table partial).
- The entity selection dropdowns MUST be populated from a companion endpoint that itself respects `accessible_to(user)` — never from a full list of entities.
- Wire this view to `/` and require authentication.

**Acceptance.**

- Signed-in user at `/` sees a working chart + table.
- Signed-out user at `/` is redirected to `/accounts/login/`.

### P5.T4 — Delete `django-plotly-dash` and legacy dashboard [serial]

**Satisfies.** `FR‑46`.

**Do.**

- Remove `django-plotly-dash`, `dash`, and any transitive-only deps from `requirements.txt`.
- Delete `dashboards/summary_dashboard.py`.
- Remove any `django_plotly_dash` entries from `INSTALLED_APPS`, `MIDDLEWARE`, `STATICFILES_FINDERS`.
- Remove any Dash-specific URL includes.

**Acceptance.**

- `grep -R 'plotly_dash\|dash_apps' .` returns zero hits.
- App boots and `/` renders without either dependency.

---

## Phase 6 — Documentation site

**Goal.** One documentation link — `/docs/` — served by the Django app. MkDocs Material powers the human docs; Swagger UI at `/docs/api/` is embedded under the API Reference section. The site is organised under **three top‑level sections**: **User Guide**, **Developer Guide**, and **API Reference** (per `FR‑52`).

**Definition of done.**

- `mkdocs.yml` at the repo root (file extension is `.yml`, not `.yaml` — the existing file on `main` uses `.yml` and the Dockerfile references `mkdocs.yml`).
- The MkDocs nav has exactly three top‑level sections: **User Guide**, **Developer Guide**, **API Reference**. No page lives at the top level outside these three sections.
- `docs/` contains one subdirectory per section (`docs/user-guide/`, `docs/developer-guide/`, `docs/api-reference/`) plus a top‑level `docs/index.md` landing page that describes the three sections and links into them.
- Every page listed in `FR‑52` under each section exists and passes `mkdocs build --strict` (no warnings, no broken links).
- Dockerfile runs `mkdocs build --strict` and copies the built site into the image.
- Django serves the built site at `/docs/` (WhiteNoise) with auth in prod.
- Swagger UI available at `/docs/api/` and reached from the API Reference section of the nav.
- CI runs `mkdocs build --strict`.
- README is under 60 lines and points at `/docs/`.

### P6.T1 — Scaffold MkDocs with the three‑section nav [serial]

**Satisfies.** `FR‑51`, `FR‑52`, `FR‑53`.

**Do.**

- `mkdocs.yml` at repo root using the Material theme, with `strict: true` and `use_directory_urls: false`.
- Restructure `docs/` into three subdirectories: `docs/user-guide/`, `docs/developer-guide/`, `docs/api-reference/`. Move existing pages into the developer guide using `git mv` (so file history is preserved) as follows:
  - `docs/architecture.md` → `docs/developer-guide/architecture.md`
  - `docs/local-dev.md` → `docs/developer-guide/local-dev.md`
  - `docs/deployment.md` → `docs/developer-guide/deployment.md`
  - `docs/roles-and-permissions.md` → `docs/developer-guide/roles-and-permissions.md`
  - `docs/ERD.md` → `docs/developer-guide/data-model.md` (or leave in place and link from developer guide)
  - `docs/getting-started.md` becomes the launcher for the User Guide (`docs/user-guide/getting-started.md`).
  - `docs/REQUIREMENTS.md` and `docs/IMPLEMENTATION_PLAN.md` are linked from the Developer Guide index; they are not moved.
- Author `docs/index.md` as a three‑card landing page that links into each section.
- Nav structure (mkdocs.yml):

  ```yaml
  nav:
    - Home: index.md
    - User Guide:
        - Overview: user-guide/index.md
        - Getting started: user-guide/getting-started.md
        - Roles at a glance: user-guide/roles.md
        - Companies & contracts: user-guide/companies-and-contracts.md
        - Orders & versions: user-guide/orders.md
        - Undertakings & cost centers: user-guide/undertakings.md
        - People & engagements: user-guide/people-and-engagements.md
        - Leaves: user-guide/leaves.md
        - Dashboard: user-guide/dashboard.md
    - Developer Guide:
        - Overview: developer-guide/index.md
        - Architecture: developer-guide/architecture.md
        - Data model: developer-guide/data-model.md
        - Roles & permissions: developer-guide/roles-and-permissions.md
        - Coding conventions: developer-guide/coding-conventions.md
        - Testing: developer-guide/testing.md
        - Local dev: developer-guide/local-dev.md
        - Deployment: developer-guide/deployment.md
        - Requirements: REQUIREMENTS.md
        - Implementation plan: IMPLEMENTATION_PLAN.md
    - API Reference:
        - Overview: api-reference/index.md
        - Using the API: api-reference/using-the-api.md
        - Swagger UI: /docs/api/
  ```

**Acceptance.**

- `mkdocs build --strict` produces a `site/` directory with no warnings.
- Every internal link resolves.
- The rendered site shows exactly three top‑level sections.
- `grep -R 'mkdocs.yaml' .` returns zero hits.

### P6.T2 — Serve MkDocs at `/docs/` from Django [serial]

**Satisfies.** `FR‑51`, `FR‑54`, `NFR‑11`.

**Do.**

- Add a Django view that serves files from the built `site/` directory. Simple approach: use `django.views.static.serve` guarded by `@login_required` in prod, or a small custom view. Do NOT proxy MkDocs' dev server — the docs ship as static files.
- Mount at `/docs/`; ensure `FORCE_SCRIPT_NAME` works (per `NFR‑26`).
- WhiteNoise MAY serve the docs directory if configured; either approach is acceptable as long as the auth requirement holds in prod.
- Update `SPECTACULAR_SETTINGS` so Swagger UI (`SpectacularSwaggerView`) is served at `/docs/api/`, replacing the earlier `/api/v1/docs/`.
- In MkDocs nav, add an entry for "API reference" that points to `/docs/api/`.

**Acceptance.**

- Signed-in user at `/docs/` sees the MkDocs site.
- Signed-out user at `/docs/` is redirected (or 401 in the API context).
- `/docs/api/` shows Swagger UI backed by `/api/v1/schema/`.

### P6.T3 — Bake docs into the Docker image [serial]

**Satisfies.** `FR‑53`.

**Do.**

- Add a `RUN mkdocs build --strict` step in the `Dockerfile` (before `collectstatic`).
- Ensure the built `site/` directory is included in the image.
- Add `mkdocs`, `mkdocs-material`, and any plugins used to a `requirements-docs.txt` (or install them at build time only).
- Update the CI workflow's `mkdocs build --strict` step to run against the same environment.

**Acceptance.**

- The production image contains `/app/site/index.html`.
- Running the container serves `/docs/` immediately (no runtime `mkdocs serve`).

### P6.T4 — Shrink README to a pointer [serial]

**Satisfies.** `NFR‑33`.

**Do.**

- README becomes short: project name, one-paragraph description, link to `/docs/` for everything else, minimal "how to run locally" (two commands) that mirrors `developer-guide/local-dev.md`.

**Acceptance.**

- README is under 60 lines.
- No architecture / permission / URL details in README that aren't also in MkDocs.

### P6.T5 — Author the User Guide [serial]

**Satisfies.** `FR‑52` (User Guide section).

**Context.** The initial P6 sweep produced developer‑oriented pages only. Business users have no on‑ramp to the app. This task authors the User Guide section from the perspective of a signed‑in non‑developer.

**Do.**

- Every page lives under `docs/user-guide/` and uses plain business language — no shell commands, no Python, no ORM references.
- Each entity workflow page follows the same shape: **Purpose** (one paragraph), **Who can do this** (which roles), **Screens** (list of the UI screens involved with paths like `/companies/`, `/orders/…/`), **Happy path** (numbered steps), **Common validation errors and how to fix them**, **Related workflows** (cross‑links).
- Pages to author, one file each:
  - `docs/user-guide/index.md` — overview: what the app is for, the three roles at a glance, how to navigate.
  - `docs/user-guide/getting-started.md` — signing in, changing your password, where the nav is.
  - `docs/user-guide/roles.md` — Admin vs. UndertakingManager vs. Person, with a table of what each can see/do. Cross‑links `developer-guide/roles-and-permissions.md` for the underlying model.
  - `docs/user-guide/companies-and-contracts.md` — creating and editing companies; adding contracts to a company; deleting.
  - `docs/user-guide/orders.md` — creating an order; adding the first version; **cloning the latest version** (the FR‑18 workflow); how versions chain start/end dates.
  - `docs/user-guide/undertakings.md` — undertakings and cost centers; assigning a manager.
  - `docs/user-guide/people-and-engagements.md` — creating a person; creating an engagement; assigning to an undertaking; assigning to an order version; FTE, start/end dates, and what happens when you edit the engagement's dates (FR‑15).
  - `docs/user-guide/leaves.md` — recording a leave; date rules (FR‑17).
  - `docs/user-guide/dashboard.md` — how to read the summary chart, what the filters do, and what "cost coverage" means to a business reader.
- Every page MUST have at least one screenshot placeholder (`![Description](images/…)`) where a screenshot would sit; do NOT fabricate images. Add a `docs/user-guide/images/.gitkeep` and a follow‑up note in the PR that screenshots are captured separately.
- Every FR that a User Guide page describes MUST be cited inline (e.g. "…per FR‑18"), so the traceability sweep in P9.T1 can grep for coverage.
- Cross‑link the Developer Guide from every page footer for readers who want to know how the workflow is implemented.

**Acceptance.**

- `mkdocs build --strict` passes with every User Guide page present in the nav.
- Every entity in `FR‑1` through `FR‑11` is covered by exactly one User Guide page (or is called out on a shared page).
- `grep -R 'FR‑' docs/user-guide/` returns at least one hit per authored page.
- No page under `docs/user-guide/` contains the strings `python manage.py`, `pytest`, `import `, or a fenced ` ```python ` block.

### P6.T6 — Fill out the Developer Guide [serial]

**Satisfies.** `FR‑52` (Developer Guide section), `NFR‑33`.

**Context.** The existing pages (`architecture.md`, `local-dev.md`, `deployment.md`, `roles-and-permissions.md`) are a stub. This task promotes them into a full developer manual under `docs/developer-guide/` and adds the missing pages.

**Do.**

- Move the pages listed in P6.T1 into `docs/developer-guide/` and update every inbound link.
- Author `docs/developer-guide/index.md` — a section landing page: how the app is organised (apps, services/selectors/managers), how to find things, links into every subsection.
- Author `docs/developer-guide/coding-conventions.md` — the rules that live today only in `.github/copilot-instructions.md`: no `print()`, services vs. selectors vs. managers, thin views, Google‑style docstrings, `mypy --strict` scope, migrations are additive, URL naming per FR‑49/FR‑50. Include a short "how to add a new entity" checklist that walks through model → manager → service → serializer → viewset → filter → UI view → nav registry → tests.
- Author `docs/developer-guide/testing.md` — the P7 regime: `factory_boy` factories, the permission‑matrix test, coverage gates from `NFR‑17`, how to run the verify loop from `.github/copilot-instructions.md`.
- Expand `docs/developer-guide/architecture.md` to include: the request lifecycle (UI vs. API), the three layers (views/services/selectors), the role model (link to `vendor_manager/roles.py`), and a Mermaid diagram of the app dependency graph.
- Expand `docs/developer-guide/data-model.md` (or link `docs/ERD.md`) so a new dev can find every entity in one place.
- Add links from `docs/developer-guide/index.md` to `REQUIREMENTS.md` and `IMPLEMENTATION_PLAN.md`.
- Add `docs/api-reference/index.md` and `docs/api-reference/using-the-api.md` as part of this task (they are technically API Reference but the authoring style — auth, pagination, filtering, custom actions — is developer‑facing).

**Acceptance.**

- Every developer‑facing page listed in `FR‑52` under "Developer Guide" exists at the path the nav references.
- `mkdocs build --strict` passes.
- A new developer can, by reading only the Developer Guide, run the app locally, add a new entity, and understand where business logic goes.
- `grep -R 'FR‑\|NFR‑' docs/developer-guide/` returns hits on the pages that describe FR/NFR‑backed behavior.

---

## Phase 7 — Test hardening

**Goal.** The test suite covers every FR/NFR listed in `NFR‑16`, the coverage gates in `NFR‑17` are enforced by CI, and factories replace ad-hoc fixture creation.

**Note.** P7 is written as a distinct phase for planning clarity, but in practice each task in P1–P6 lands with its own tests. This phase is the *finishing sweep* that fills gaps and turns on the diff-coverage gate.

**Definition of done.**

- Overall line coverage ≥ 80%; `services`, `selectors`, `permissions`, `api`, `serializers` ≥ 90%.
- Diff coverage ≥ 80% gate is active on PRs (from P0.T3, unmuted here if it was muted).
- Every model invariant (FR‑12–FR‑17) has a test.
- Every viewset has role-personas tests for each of Admin, UndertakingManager, Person.
- No SQL-dump fixtures; every test builds data via `factory_boy`.

### P7.T1 — Introduce `factory_boy` factories [serial]

**Satisfies.** `NFR‑19`.

**Do.**

- Create `<app>/tests/factories.py` for each app with `factory.django.DjangoModelFactory` classes.
- Wire factories to produce coherent objects (e.g. `EngagementFactory` uses `PersonFactory`; date fields default to sensible ranges).
- Delete any SQL-dump / JSON fixture that is used by tests (there should be none in this repo today; verify).

**Acceptance.**

- `grep -R 'loaddata\|.sql' **/tests/` returns zero hits.
- Every test file imports from `<app>/tests/factories.py`.

### P7.T2 — Model invariant tests [per-app, parallel-safe]

**Satisfies.** `FR‑12`–`FR‑17`.

**Do.**

- `engagements/tests/test_models.py`: FTE range (FR‑12), FR‑13, FR‑14, FR‑15.
- `orders/tests/test_models.py`: FR‑16 (start ≤ end; gap-free versions; no overlap).
- `leaves/tests/test_models.py`: FR‑17.
- Every test creates data via factories; every test asserts a `ValidationError` or an accepted create.

**Acceptance.**

- Every FR in the range has at least one dedicated test method.

### P7.T3 — Service tests [serial]

**Satisfies.** `NFR‑16`.

**Do.**

- `orders/tests/test_services.py`: full coverage of `create_new_order_version`, including transactional rollback.
- `engagements/tests/test_selectors.py`: cost / cost_coverage on a fixed dataset; the expected output is checked in as a JSON snapshot.

**Acceptance.**

- Snapshot output does not change between test runs.
- Rollback test verifies no `OrderVersion` row remains after a forced mid-transaction failure.

### P7.T4 — API tests per role [per-viewset, parallel-safe]

**Satisfies.** `NFR‑16` (per-endpoint × three-role coverage).

**Do.**

- For each viewset, a test class that uses DRF's `APIClient` with each of the three roles.
- Covers: list, retrieve, create, update, partial_update, delete, plus every custom `@action` from FR‑31.
- Both Basic and session auth are exercised at least once per role somewhere in the suite.

**Acceptance.**

- Every viewset in `/api/v1/` has a matching test class.
- The coverage report shows `api.py`, `serializers.py`, `services.py`, `selectors.py`, `permissions.py` all ≥ 90%.

### P7.T5 — Permission-matrix tests [serial]

**Satisfies.** `FR‑25`, `FR‑26`, `FR‑27`, `FR‑28`.

**Do.**

- One test module `tests/test_permission_matrix.py` (or under `vendor_manager/tests/`) that iterates over every `(role, entity, verb)` triple and asserts the expected HTTP status.
- Parameterize with `pytest.mark.parametrize`.
- Also assert that `Entity.objects.accessible_to(user)` matches the set of entities for which the object-level check `access_<entity>(user, e)` returns `True`.

**Acceptance.**

- Adding a new entity requires one new row in the parametrization to be added; the test framework enforces coverage.

### P7.T6 — Dashboard access-control tests [serial]

**Satisfies.** `FR‑45`, `NFR‑16`.

**Do.**

- Fixture: two `Person`s, each with an `Engagement`. A `Person`-role user on the dashboard MUST see only their own aggregates. Verify: totals, per-period sums, entity dropdown contents.

**Acceptance.**

- Test fails if `dashboards/selectors.py` is edited to bypass `accessible_to(user)`.

### P7.T7 — Turn on the diff-coverage gate [serial]

**Satisfies.** `NFR‑17`.

**Do.**

- If the diff-coverage step in `.github/workflows/ci.yaml` was configured as informational during P0.T3, flip it to *failing* now.
- Verify by opening a scratch PR with an under-covered diff — CI must fail.

**Acceptance.**

- The gate is enforced; a PR with <80% diff coverage cannot be merged.

---

## Phase 8 — Strict-typing sweep

**Goal.** Every remaining Python file in the project is annotated to satisfy `mypy --strict`. The mypy `files` list expands to cover the whole project (minus migrations and generated code).

**Definition of done.**

- `mypy --strict` (project-wide) reports zero errors in CI.
- No new `# type: ignore` comments outside a small, documented list.
- Every public function, method, and non-field class attribute is annotated.

### P8.T1 — Expand `mypy` scope to the whole project [serial]

**Satisfies.** `NFR‑30`.

**Do.**

- Remove the P0.T4 module allowlist; make `mypy` run over the whole project except `migrations/` and `staticfiles/`.
- Expect a flurry of errors. Do not add ignores. Fix each error.
- `django-stubs` plugin config is critical here — verify `django_settings_module` still points at the right settings.

**Acceptance.**

- `mypy` in CI runs against the full project and passes.

### P8.T2 — Annotate services, selectors, serializers, viewsets first [parallel-safe]

**Satisfies.** `NFR‑30`.

**Do.**

- These are the highest-ROI modules for typing (they're the layer other modules import). Annotate them completely first.
- Every service function: parameter types + return type.
- Every selector: parameter types + return type (use `TypedDict` for the shapes returned to the dashboard).
- Every serializer: `class Meta` with typed `fields`; explicit field types.
- Every viewset: `queryset` and `serializer_class` annotations; `perform_create`, `perform_update` typed.

**Acceptance.**

- `mypy` errors under these modules drop to zero first.

### P8.T3 — Annotate remaining app code [per-app, parallel-safe]

**Satisfies.** `NFR‑30`.

**Do.**

- `views.py`, `forms.py`, `tables.py`, `filters.py`, `permissions.py`, `admin.py`, `urls.py`.
- For Django model fields, rely on `django-stubs` inference; only annotate class attributes that aren't fields.

**Acceptance.**

- `mypy --strict` reports zero errors on every app package.

### P8.T4 — Annotate tests and factories [parallel-safe]

**Satisfies.** `NFR‑30`.

**Do.**

- Tests count. Type them.
- Factories: `factory_boy` types are imperfect; a small `# type: ignore[misc]` on the metaclass is acceptable if unavoidable — document each in a `docs/mypy-decisions.md` note (created under Phase 6's docs section).

**Acceptance.**

- `mypy --strict` is zero-error project-wide.
- The list of `# type: ignore` comments in the codebase is small and each is annotated with a reason.

---

## Phase 9 — Acceptance & release

**Goal.** Every requirement is demonstrated by a passing test, `check --deploy` is clean, MkDocs builds, and the k3s deploy completes green from a `v1.0.0` tag.

### P9.T1 — Requirements traceability matrix [serial]

**Satisfies.** All FR/NFR.

**Do.**

- Author `docs/traceability.md` (linked from MkDocs nav) that lists every `FR‑*` and `NFR‑*` and points to the test module(s) that cover it.
- Any FR/NFR without a corresponding test is a defect — open a task, complete it, then continue.

**Acceptance.**

- Every FR and NFR appears in the matrix with at least one test reference.

### P9.T2 — `check --deploy` zero warnings under prod profile [serial]

**Satisfies.** `NFR‑15`.

**Do.**

- Boot the app with the production `SETTINGS_MODULE` and env, run `python manage.py check --deploy`, and drive the warning count to zero. Common culprits: `SECURE_HSTS_SECONDS`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, `X_FRAME_OPTIONS`.

**Acceptance.**

- CI's `check --deploy` step passes.

### P9.T3 — Full dry-run release [serial]

**Satisfies.** `NFR‑24a`.

**Do.**

- Cut a `v1.0.0` tag against a staging branch. Watch `.github/workflows/deploy.yaml` execute end to end: build → push to Docker Hub → `deploy-to-k3s` action → k3s rollout with the migration `initContainer` and `/health/` probes.
- Verify the rolled-out pod passes readiness within 30 seconds and stays ready.
- Against the staging URL, run `python scripts/populate.py --base-url <staging-url> --user <admin> --password <pw> --reset --seed 42` (P3.T6) and confirm it completes green. This is the release-time smoke test that proves every API endpoint is functional against the freshly-deployed image.

**Acceptance.**

- The staging namespace shows the new tag serving requests.
- Rollback via a new `workflow_dispatch` with the previous tag succeeds.
- The populate script's summary line matches the expected entity counts.

### P9.T4 — Freeze and cut `v1.0.0` [serial]

**Satisfies.** Acceptance criteria in `docs/REQUIREMENTS.md` §6.

**Do.**

- Walk `docs/REQUIREMENTS.md` §6 (acceptance criteria 1–12) point by point; every one MUST be demonstrable.
- Merge to `main`. Cut `v1.0.0` release.

**Acceptance.**

- Every acceptance criterion in §6 is verified.
- The `docs/traceability.md` matrix has no gaps.

---

## Cross-cutting rules for agents

- **No behavior changes in refactor commits.** If a task both moves code and fixes a bug, split them.
- **Never edit a migration file that has already been applied to production.** Add a new migration instead.
- **Never introduce a new top-level dependency without adding it to `requirements.txt` and justifying it in the commit message.**
- **Never bypass CI locally with `--no-verify`.** If a hook is wrong, fix the hook.
- **Prefer deleting code to adding code.** This refactor's success is measured in *lines removed*.
- **When in doubt, ask via the "Open issues" section below.**

---

## Open issues during execution

*(Agents append blockers, ambiguities, or discoveries here as they work. Every entry MUST have an owner and a status. Resolved entries stay, marked `RESOLVED`, as a decision log.)*

*(none yet)*
