# Vendor Manager — Functional & Non‑Functional Requirements

**Status:** Draft v1 — prepared for the "best‑Django‑practices" refactor.
**Scope:** Requirements for the refactored application. The refactor preserves the current entity‑relationship model (see [docs/ERD.md](ERD.md)) and the current minimalist, database‑table‑style user experience. It restructures the codebase to eliminate template and view redundancy, introduces a proper REST API that covers every user action, and adds meaningful test coverage.

---

## 1. Context

Vendor Manager is a Django 5.1+ application for tracking vendors, contracts, orders, order versions, people, engagements, assignments, undertakings and leaves. The current implementation is functional but suffers from significant duplication in templates and views, dormant DRF configuration, missing tests, and a rename‑cycle migration history.

### 1.1 Preserved
- The relational data model (ERD) — see [docs/ERD.md](ERD.md).
- The minimalist, "database‑like" UI: tabular lists, plain forms, detail pages that show record fields and related records.
- The `Person`‑to‑`auth.User` OneToOne mapping (no custom user model).
- Docker Compose as the primary deployment path.
- Sub‑path hosting via `FORCE_SCRIPT_NAME`.

### 1.2 Explicitly changed
- Templates are consolidated behind a small set of reusable generic templates and partials.
- Every user action becomes reachable via a REST API of equal capability (feature parity between UI and API).
- Business logic moves out of views and out of fat model methods into an explicit services/selectors layer where it improves clarity or testability.
- Migration history is squashed to remove rename cycles.
- Meaningful tests are added (models, services, API, permissions).

### 1.3 Out of scope
- Any change to the ERD.
- Migration to a custom `User` model.
- Rebuilding the UI as a JavaScript SPA. The frontend remains server‑rendered Django templates.
- Redesign of the visual style beyond consistent, non‑inline CSS. The DB‑table aesthetic stays.
- New business domains or new entities.

---

## 2. Guiding Principles

1. **ERD is immutable.** Field types, keys and relationships defined in [docs/ERD.md](ERD.md) do not change. Only Python‑level structure (managers, methods, meta options, services, forms, views, templates) is refactored.
2. **Single source of truth for behavior.** Every business operation is implemented once (services layer) and exposed twice — once through DRF and once through the server‑rendered UI views — without duplicating logic.
3. **DRY templates.** No two apps ship near‑duplicate `add_x.html` / `edit_x.html` / `all_x.html` templates. Shared shape lives in generic templates; per‑entity concerns are declared, not copy‑pasted.
4. **Explicit over implicit.** No `fields = "__all__"` in forms/serializers, no wildcard imports, no in‑view permission monkey‑patching.
5. **Thin views, fat services, calm models.** Views orchestrate. Services encapsulate multi‑step business rules. Models express structure, invariants and simple derived properties.
6. **The API is not a bonus.** Anything a signed‑in user can do through the UI must be doable via the API with the same authorization semantics.
7. **The UI remains minimalist.** Tables, plain forms, no dashboard chrome, no framework CSS beyond a small utility layer. Users should still feel like they are looking at a database.

---

## 3. Functional Requirements

Requirements are prefixed `FR‑`. Each is testable.

### 3.1 Domain entities (CRUD parity across UI and API)

For each entity below, the system MUST provide list, retrieve, create, update and delete operations, exposed as:
- Server‑rendered UI pages (list, detail, add form, edit form, delete confirmation flow).
- REST API endpoints under `/api/v1/` following DRF conventions (`GET`, `POST`, `PUT/PATCH`, `DELETE`), returning JSON.

Entities in scope:

| # | Entity | Notes |
|---|---|---|
| FR‑1 | `Company` | Business‑assigned integer PK preserved. |
| FR‑2 | `Contract` | Business‑assigned integer PK preserved. |
| FR‑3 | `Person` | Business‑assigned string PK (max 6). OneToOne with `auth.User`. |
| FR‑4 | `Order` | Business‑assigned integer PK. Belongs to `Company`. |
| FR‑5 | `OrderVersion` | Belongs to `Order`, links to `Contract`. Preserves temporal invariants (see FR‑16). |
| FR‑6 | `Undertaking` | Business‑assigned integer PK. Has `CostCenter` and `Person` (manager). |
| FR‑7 | `CostCenter` | Business‑assigned integer PK. |
| FR‑8 | `Engagement` | Auto PK. Belongs to `Person`. |
| FR‑9 | `EngagementOrderVersionAssignment` | Junction of `Engagement` × `OrderVersion`. |
| FR‑10 | `EngagementUndertakingAssignment` | Junction of `Engagement` × `Undertaking`, dated, percentage‑weighted. |
| FR‑11 | `Leave` | Belongs to `Person`, dated, percentage‑weighted. |

### 3.2 Business‑rule requirements

- **FR‑12** `Engagement.fte` MUST be in `[0, 1]`. Invalid values are rejected at both API and UI boundaries with a readable error.
- **FR‑13** An `EngagementOrderVersionAssignment` MUST only be creatable when `engagement.order == order_version.order` (single‑order constraint). Attempting otherwise MUST return a validation error.
- **FR‑14** An `EngagementUndertakingAssignment` MUST fall entirely within its engagement's `[start_date, end_date]`, and MUST NOT overlap with another assignment of the same `(engagement, undertaking)` pair.
- **FR‑15** When an `Engagement` is saved, existing `EngagementUndertakingAssignment` records MUST be adjusted so that their date ranges remain inside the engagement's date range.
- **FR‑16** `OrderVersion` MUST enforce, on both create and update:
  - `start_date <= end_date`;
  - version numbers within an `Order` are gap‑free;
  - version date ranges within an `Order` do not overlap.
- **FR‑17** A `Leave.percentage` MUST be in `[0, 1]`.
- **FR‑18** `Order.create_new_version(...)` MUST remain atomic; either the new `OrderVersion` and any copied assignments are all committed, or nothing is. This operation MUST be reachable via:
  - a dedicated UI action ("Clone latest version") on the order detail page, and
  - a dedicated API endpoint (e.g. `POST /api/v1/orders/{id}/versions/clone-latest/`).
- **FR‑19** `Engagement.costs` and `Engagement.cost_coverage` MUST continue to produce the same per‑date output as today (daily cost = `daily_rate × fte × availability` on days covered by an active `OrderVersion` assignment, reduced by overlapping `Leave` percentage; coverage totals capped at 100% and gaps labelled "unassigned").
- **FR‑20** The summary dashboard (currently in `dashboards/summary_dashboard.py`) MUST continue to support filtering by `class_` ∈ {Engagement, Undertaking, Person, Order, Company}, by granularity ∈ {Daily, Monthly, Total}, by date range, and by entity‑specific selections. Output MUST include both a Plotly chart and a tabular view.

### 3.3 Authentication and session

- **FR‑21** The UI MUST provide a login page at `/accounts/login/` and logout.
- **FR‑22** Users MUST authenticate with a username and password. The API MUST accept HTTP Basic authentication so that external clients (including `curl` and scripts) can call any endpoint with `-u user:pass`. Session authentication MAY additionally be enabled to support the same‑origin UI. Token / JWT authentication is NOT required. The specific authentication classes (DRF's built‑ins or equivalent) are an implementation choice; the observable behavior above is what matters.
- **FR‑23** A signed‑in user MUST have exactly one linked `Person`. Users without a linked `Person` MUST be blocked at login (UI) and receive `403 Forbidden` from any authenticated API call, with a clear error message. (Preserves current `check_user_person_assignment` behavior.)
- **FR‑24** Password reset flows are not required in this phase; the built‑in Django URLs may be exposed but are not a hard requirement.

### 3.4 Authorization

- **FR‑25** The application MUST expose exactly three roles: `Person`, `UndertakingManager`, `Admin`. The current implementation uses `django-role-permissions`; the refactor MAY keep it or replace it with any equivalent mechanism (Django groups + permissions, `django-rules`, etc.) provided the three‑role model, the permission matrix currently declared in `vendor_manager/roles.py`, and the per‑entity object‑level semantics of §3.4 are preserved. Inconsistent permission names (e.g. `view_engagement_undertaking_version_assignment` vs `..._undertaking_assignment`) MUST be reconciled to a single canonical set.
- **FR‑26** Every entity MUST have a single `access_<entity>` object‑level checker with identical semantics for API and UI. There MUST be no duplicated per‑surface implementation.
- **FR‑27** UI list views MUST only show items the user can access. API list endpoints MUST filter identically. Direct URL access to a non‑accessible item MUST return 403 (UI) / 403 (API), never 404 masking access.
- **FR‑28** Object‑level access checks MUST be enforceable at the ORM level (queryset filter) so that list endpoints do not have to iterate in Python. (See NFR‑7.)

### 3.5 API surface

- **FR‑29** The REST API MUST be namespaced under `/api/v1/`.
- **FR‑30** Every entity in §3.1 MUST be exposed as a DRF `ModelViewSet` with an explicit `Serializer` (no `fields = "__all__"`; every field is listed).
- **FR‑31** Custom (non‑CRUD) actions MUST be modelled as `@action` on the corresponding viewset — at minimum:
  - `POST /api/v1/orders/{id}/versions/clone-latest/` (see FR‑18);
  - `GET  /api/v1/engagements/{id}/costs/`;
  - `GET  /api/v1/engagements/{id}/cost-coverage/`;
  - `GET  /api/v1/people/{id}/assignments/`.
- **FR‑32** The API MUST return validation errors from model/service layer validation with HTTP 400 and DRF's standard error shape.
- **FR‑33** The API MUST use pagination on list endpoints (page‑number pagination, default page size 50, max 200).
- **FR‑34** The API MUST support at least: filtering by primary key relations (e.g. `?company=…` on orders), ordering (`?ordering=…`), and search on human‑readable fields (`?search=…`) via `django-filter` and DRF's `SearchFilter`/`OrderingFilter`.
- **FR‑35** The API MUST publish an OpenAPI schema (via `drf-spectacular` or equivalent) at `/api/v1/schema/`. The browsable Swagger UI MUST be reachable at `/docs/api/` and MUST be linked from the MkDocs navigation (see §3.10) so that the entire documentation surface is behind a single top‑level `/docs/` link. Both endpoints are reachable in production but MUST require authentication (username + password, per FR‑22); they are NOT staff‑gated beyond that.

### 3.6 Server‑rendered UI

- **FR‑36** The UI MUST cover the same operations as the API. No API‑only feature.
- **FR‑37** There MUST be exactly one base template (`base.html`) and one generic set of CRUD templates:
  - `_list.html` — table of records with add/edit/delete controls;
  - `_detail.html` — record fields + related record blocks;
  - `_form.html` — used for both create and edit.

  Per‑entity templates only exist to declare *what* is shown (columns, related blocks), never to re‑implement *how*.
- **FR‑38** Forms MUST be rendered through `django-crispy-forms` with a single project‑wide template pack. Tables MUST be rendered through `django-tables2` (or an equivalent shared partial) with per‑entity `Table` classes.
- **FR‑39** The sidebar navigation MUST be data‑driven from a single navigation registry, not hard‑coded per link, so adding an entity is a one‑line change.
- **FR‑40** UI delete actions MUST go through an intermediate confirmation page (a `GET` on `.../delete/` renders a confirm view; a `POST` from that page performs the deletion). This avoids relying on JS `confirm()` and works without JavaScript. The confirmation page MUST be a single shared template.
- **FR‑41** Flash messages MUST continue to be rendered from `django.contrib.messages` in a single location in `base.html`.
- **FR‑42** All styling MUST come from CSS files under `static/`. No `style="..."` attributes and no `border="1"` on tables in templates.

### 3.7 Dashboards

- **FR‑43** The summary dashboard MUST remain reachable at the site root (`/`) for signed‑in users.
- **FR‑44** The dashboard's data preparation MUST live in a service (`dashboards/services.py`) backed by selectors in `dashboards/selectors.py`, not on model classes, and MUST be callable from tests without spinning up any UI layer.
- **FR‑45** The dashboard MUST enforce the same object‑level access control as the rest of the application (FR‑26, FR‑27, FR‑28). Concretely: the dashboard's selectors MUST filter every underlying queryset through `<Entity>QuerySet.accessible_to(user)` before any aggregation. Aggregates (totals, per‑period sums, per‑entity breakdowns) MUST be computed only over rows the acting user can access. A restricted user MUST NOT be able to infer the existence, identity, or magnitude of records they cannot access — including through aggregate totals, chart shapes, or entity dropdowns. The dashboard MUST NOT expose entity selectors (dropdowns of Person, Undertaking, Order, Company, Engagement) whose values include entities the user cannot access.
- **FR‑46** The dashboard MUST be re‑implemented as: (a) a JSON API endpoint under `/api/v1/dashboards/summary/` that accepts the same filters as the current dashboard (`class_`, granularity, date range, entity selection) and returns pre‑aggregated series data + a tabular breakdown, subject to FR‑45; and (b) a minimal server‑rendered Django template at `/` that fetches from that endpoint and renders the chart with Plotly.js and the table with `django-tables2` (or the shared table partial from FR‑38). The `django-plotly-dash` dependency and the current `dashboards/summary_dashboard.py` Dash app MUST be removed as part of this rework.
- **FR‑47** The dashboard summary endpoint MUST continue to support filtering by `class_` ∈ {Engagement, Undertaking, Person, Order, Company}, by granularity ∈ {Daily, Monthly, Total}, by date range, and by entity‑specific selections — with each of these filters honoring the access‑control constraint in FR‑45.

### 3.8 Admin

- **FR‑48** Every model MUST be registered in `admin.py` with an explicit `ModelAdmin` declaring `list_display`, `search_fields`, and `list_filter` where meaningful. No bare `admin.site.register(Model)`.

### 3.9 URLs

- **FR‑49** URL patterns MUST follow standard REST conventions: trailing slashes on all paths; plural collection URLs (`companies/`), singular member URLs with an ID segment (`companies/<id>/`). Sub‑resources use nested paths (e.g. `engagements/<id>/undertaking-assignments/`). Assignment endpoints under an engagement MUST use the nested shape for the UI‑facing form; a flat, filterable endpoint (e.g. `/api/v1/engagement-undertaking-assignments/?engagement=<id>`) MAY additionally be exposed for reporting. Any URL in the current codebase that does not fit this convention MUST be corrected as part of the refactor, even if not individually listed here — mis‑organized URLs are treated as defects to fix.
- **FR‑50** URL name conventions MUST be consistent (`company-list`, `company-detail`, `company-create`, `company-update`, `company-delete`) and used everywhere `reverse()` is called.

### 3.10 Documentation

- **FR‑51** The project MUST publish a single documentation site built with MkDocs (Material theme recommended) and served by the Django app at `/docs/`. `/docs/` is the single entry point users see; the README and any other developer‑facing markdown MUST link to it and MUST NOT duplicate its content.
- **FR‑52** The MkDocs site MUST be organized under **three top‑level sections** — **User Guide**, **Developer Guide**, and **API Reference** — and MUST include, at minimum, the following pages:
  - **User Guide** (business‑user perspective; no code, no shell commands):
    - Overview / what the app is for.
    - Signing in and the three roles (`Admin`, `UndertakingManager`, `Person`) — what each role can see and do.
    - Managing companies and contracts (day‑to‑day workflows).
    - Managing orders and order versions, including how to clone a version.
    - Managing undertakings and cost centers.
    - Managing people and engagements (assignment lifecycle, FTE, dates).
    - Recording and reviewing leaves.
    - Reading the dashboard (filters, granularity, entity selection).
    - Every workflow section MUST document the happy path with numbered steps and at least one screenshot placeholder (`![](images/…)`); error / validation messages that a user can hit MUST be listed with the corrective action.
  - **Developer Guide** (contributor perspective):
    - Architecture (apps, services/selectors/managers split, UI vs. API split).
    - Data model (embedding or linking [docs/ERD.md](ERD.md)).
    - Role & permission model (linking `vendor_manager/roles.py` and the permission‑matrix test).
    - Local dev setup (the two dev modes from `NFR‑24`: Docker Compose + pure SQLite).
    - Coding conventions (services vs. selectors vs. managers, thin views, no `print()`, docstring style, `mypy --strict`).
    - Testing guide (`factory_boy` factories, permission‑matrix tests, coverage gates from `NFR‑17`).
    - Deployment (see §4.6, the k3s pipeline per `NFR‑24a`).
    - The Requirements document (this file) and the Implementation Plan MUST be linked from here.
  - **API Reference**: a landing page that embeds or directly links the Swagger UI at `/docs/api/`, which in turn is backed by the OpenAPI schema at `/api/v1/schema/` (FR‑35). This section MUST also include a short "using the API" primer covering Basic auth, pagination, filtering, and the custom `@action` endpoints from FR‑31.
- **FR‑53** The MkDocs site MUST be built as part of the CI pipeline (build‑only check on PRs; broken links and unresolved cross‑references MUST fail CI) and MUST be built into the production Docker image so it is served by the same process as the app. No separate docs host / no external docs URL.
- **FR‑54** The MkDocs site MUST require authentication in production (same rule as FR‑35 / NFR‑11): reachable but not public. In local dev it MAY be served unauthenticated.

---

## 4. Non‑Functional Requirements

Requirements are prefixed `NFR‑`.

### 4.1 Architecture and code organization

- **NFR‑1** Per‑app layout MUST be: `models.py`, `managers.py` (where custom querysets are needed), `services.py` (write operations), `selectors.py` (read/query operations) where either is non‑trivial, `serializers.py`, `api.py` (viewsets), `views.py` (UI views only), `forms.py`, `tables.py`, `admin.py`, `urls.py`, `permissions.py`, `tests/`.
- **NFR‑2** UI views and API viewsets MUST both call the same services/selectors. There MUST be no duplicated business logic between them.
- **NFR‑3** No business logic in templates. Templates only display data provided by the view.
- **NFR‑4** No cross‑app imports of internal helpers except through public interfaces (`app/services.py`, `app/selectors.py`, `app/api.py`).
- **NFR‑5** Cyclomatic complexity and duplication MUST be reduced from current baseline; specifically, the four templates `add_company.html`, `add_contract.html`, `add_person.html`, `add_undertaking.html` MUST collapse to zero (all served by `_form.html`), and the equivalent for `all_*.html` and `*_details.html`.

### 4.2 Performance (target scale: <50 concurrent users, <10 000 rows per table)

- **NFR‑6** A list page or list API endpoint MUST serve a full page within 500 ms server‑time at the target scale on the reference dev container.
- **NFR‑7** Permission‑filtered list queries MUST NOT scan every row in Python. `access_<entity>` MUST have a queryset counterpart (e.g. `<Entity>QuerySet.accessible_to(user)`) used by both the UI and the API.
- **NFR‑8** Detail pages MUST use `select_related` / `prefetch_related` for related blocks (no N+1 in the reference queries).
- **NFR‑9** The dashboard data pipeline MUST cache the full cost DataFrame for the duration of a session unless the user explicitly requests recalculation (preserves current behavior). Cache invalidation on writes is not required in this phase.

### 4.3 Security

- **NFR‑10** All UI mutating endpoints MUST require CSRF. The API MUST require CSRF only when the caller is authenticated via a session cookie; requests authenticated with HTTP Basic (FR‑22) MUST NOT be subject to CSRF (standard DRF behavior for non‑session auth classes). The current `@csrf_exempt` on `login_api` MUST be removed and the hand‑rolled JSON login view retired in favor of DRF's authentication classes.
- **NFR‑11** All views (UI and API) MUST require authentication except the login page, static files, and `/health/`. The OpenAPI schema (`/api/v1/schema/`), the browsable API UI (`/docs/api/`), and the MkDocs site (`/docs/`) are reachable in production but MUST require authentication — they are not public (per FR‑35, FR‑54).
- **NFR‑12** No secret MAY be committed. `DJANGO_SECRET_KEY`, database credentials, and any tokens MUST be read from environment.
- **NFR‑13** `DEBUG` MUST default to `False` when the env var is unset or empty. (Current code assigns the raw string, which is truthy.)
- **NFR‑14** `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` MUST be configured from environment for production.
- **NFR‑15** The application MUST pass `python manage.py check --deploy` with zero warnings under the production configuration.

### 4.4 Testing

- **NFR‑16** Test suite MUST cover, at minimum:
  - all model invariants listed in §3.2 (FR‑12 through FR‑17);
  - the `Order.create_new_version` service (happy path + failure modes);
  - the cost / cost‑coverage calculations (fixture‑based, deterministic);
  - every API endpoint from §3.5 (list, retrieve, create, update, delete, custom actions), with three role personas (Admin, UndertakingManager, Person);
  - permission matrix per role per entity (positive and negative cases);
  - the dashboard summary endpoint (FR‑46), including access‑control cases: a `Person`‑role user MUST NOT see aggregates that include entities they cannot access.
- **NFR‑17** Test coverage MUST meet BOTH gates in CI:
  - **Overall line coverage ≥ 80%** across the project, with `services`, `selectors`, `permissions`, `api`, and `serializers` at ≥ 90%.
  - **Diff coverage ≥ 80%** on every pull request — i.e. of the lines changed in the PR, at least 80% MUST be covered by tests. This is enforced by a tool such as `diff-cover` in CI. Legacy uncovered code does not block a PR, but new/changed code does.
- **NFR‑18** Tests MUST run against SQLite in CI in under 60 seconds at current entity count.
- **NFR‑19** Factories (`factory_boy` or similar) SHOULD be used to build test data; fixtures via SQL dumps MUST NOT be used.

### 4.5 Migrations

- **NFR‑20** Migration history MUST be squashed per app to remove rename cycles. Post‑squash, each app MUST start from a clean `0001_initial` (or a squashed initial) with a linear, forward‑only history.
- **NFR‑21** Business‑assigned primary keys (`Company.id`, `Contract.id`, `Person.id`, `Order.id`, `Undertaking.id`, `CostCenter.id`) MUST remain as they are today. This is a deliberate choice — do not migrate them to auto PKs.
- **NFR‑22** New migrations MUST be reviewed for reversibility. `migrate --plan` MUST show a linear plan with no `RunPython` operations that lack a `reverse_code` unless justified in a comment.

### 4.6 Deployment and operations

- **NFR‑23** The application MUST support exactly two database backends: PostgreSQL (production and the default in Docker Compose dev) and SQLite (lightweight local dev and CI). MSSQL support MUST be removed from `settings.py`, `requirements.txt`, and any Docker configuration. No other database backends are in scope.
- **NFR‑24** Local development MUST support two modes:
  1. **Compose‑DB + host‑app** (default): `docker compose up` in [compose.yml](https://github.com/durczokj/vendor_manager/blob/main/compose.yml) brings up PostgreSQL only; the Django app runs on the host via `python manage.py runserver`.
  2. **Pure SQLite** (no containers at all): `python manage.py runserver` with the SQLite settings profile selected via env var.

  The current unused `docker-compose.prod.yml` MUST be deleted from the repository as part of the refactor — production runs on k3s (NFR‑24a), not on Docker Compose, and keeping the file invites confusion.
- **NFR‑24a** Production runs on **k3s** (lightweight Kubernetes). Continuous deployment MUST run on GitHub release (event `release: published`) and MAY additionally be dispatched manually via `workflow_dispatch` with an explicit tag input. The current [.github/workflows/deploy.yaml](https://github.com/durczokj/vendor_manager/blob/main/.github/workflows/deploy.yaml) already implements this shape and MUST be maintained, not replaced. Concretely, the CD workflow MUST:
  - Build the production Docker image from the repo `Dockerfile` and push it to **Docker Hub** (`durczokj/vendor-manager:<tag>`) using the resolved tag (release tag name, or the `workflow_dispatch` `tag` input). The image MUST be tagged with an immutable version tag; `:latest` MUST NOT be relied on by any deployment manifest.
  - Deploy to the k3s cluster via the reusable composite action `durczokj/vm/.github/actions/deploy-to-k3s@main`, passing `app_name`, `deployment_name`, `image_tag`, and the SSH credentials. Cluster‑side manifests (`Service`, `Ingress`, `ConfigMap`, `Secret`, `Namespace`) are the responsibility of that action and its supporting repo; they MUST NOT be duplicated in this repo.
  - The Kubernetes `Deployment` manifest lives at [deploy/k8s/deployment.yaml](https://github.com/durczokj/vendor_manager/blob/main/deploy/k8s/deployment.yaml) and MUST use `__IMAGE_TAG__` as the substitution placeholder that the deploy action replaces with the resolved tag. The manifest MUST include an `initContainer` that runs `python manage.py migrate --noinput` before the app container starts, so migrations are part of every deploy.
  - The manifest MUST define `readinessProbe` and `livenessProbe` against the app's `/health/` endpoint (see NFR‑39).
  - All required credentials (`DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`, `SERVER_HOST`, `SERVER_USER`, `SERVER_SSH_KEY`) MUST come from GitHub Actions secrets. No secrets in the repository.
  - CI MUST fail the workflow if the build, push, or k3s rollout fails. Rollback is performed by re‑dispatching the workflow (`workflow_dispatch`) with the previous known‑good tag.
- **NFR‑25** Static files MUST continue to be served by WhiteNoise with `CompressedManifestStaticFilesStorage`.
- **NFR‑26** Sub‑path hosting via `FORCE_SCRIPT_NAME` MUST continue to work; all internal links MUST use `{% url %}` / `reverse()`, never hard‑coded paths (currently `/companies/`, `/contracts/` etc. are hard‑coded in some templates and MUST be removed).
- **NFR‑27** Logging MUST be configured to write to stdout in a structured format compatible with container log collection (JSON or logfmt). No `print()` in application code.
- **NFR‑28** The `login_api` `print(...)` debug decorator in `vendor_manager/views.py` MUST be removed.

### 4.7 Code quality and tooling

- **NFR‑29** The project MUST use **Ruff** for both linting and formatting (Ruff's formatter is Black‑compatible). Black and `isort` MUST be removed from `.pre-commit-config.yaml` and from any dev dependency. CI MUST run `ruff check` and `ruff format --check` and MUST fail on any error.
- **NFR‑30** The project MUST enforce **strict** static type checking with `mypy --strict` across the entire codebase (app packages, services, selectors, serializers, viewsets, forms, tables, permissions, admin, and utility modules). Django and DRF integration MUST use `django-stubs` and `djangorestframework-stubs` with an appropriate `django-stubs` settings module hint. Every function, method, and classmethod (including `__init__`, `save`, `clean`, DRF `perform_*` hooks, and services) MUST have complete parameter and return type annotations. Every class attribute that is not a Django model field MUST be annotated. Migrations, third‑party stubs, and generated code MAY be excluded via `mypy` config. CI MUST fail on any `mypy` error.
- **NFR‑31** The CI pipeline (GitHub Actions) MUST run, on every pull request and on every push to `main`, at minimum:
  1. `ruff check .`
  2. `ruff format --check .`
  3. `mypy --strict` (project scope, per NFR‑30)
  4. `pytest` (with coverage) — gated by BOTH the overall and diff‑coverage thresholds in NFR‑17
  5. `python manage.py check --deploy` under the production settings profile (see NFR‑15)
  6. `mkdocs build --strict` (see FR‑53)

  Any failure in any step MUST fail the workflow. The CI MUST run against the pinned Python version used in production.
- **NFR‑32** A `pre-commit` config MUST run `ruff check`, `ruff format`, `django-upgrade`, and `check --deploy` locally. `mypy --strict` MAY additionally run in pre‑commit but is not required (CI is the source of truth).
- **NFR‑33** The README MUST be short and MUST redirect users to the MkDocs site (FR‑51). Detailed documentation MUST live in MkDocs, not in the README.

### 4.8 Accessibility and UX (minimal)

- **NFR‑34** Every form field MUST render with an associated `<label>` (crispy‑forms handles this by default).
- **NFR‑35** Every action button MUST be a real `<button>` or `<a>`, keyboard‑reachable. No pure `onclick` divs.
- **NFR‑36** The DB‑table aesthetic is preserved; no visual redesign is required. But: fixed 20% / 80% flex layout MUST be replaced with a rule that does not break on narrow terminals (min‑widths, no overflow of the content column).

### 4.9 Observability

- **NFR‑37** Request logging MUST include the acting user's id for authenticated requests.
- **NFR‑38** Unhandled exceptions MUST be logged with traceback at `ERROR` level.
- **NFR‑39** A `/health/` endpoint (unauthenticated, returns 200 + DB ping) MUST be provided for container health checks. The Kubernetes `readinessProbe` and `livenessProbe` in [deploy/k8s/deployment.yaml](https://github.com/durczokj/vendor_manager/blob/main/deploy/k8s/deployment.yaml) already target this path (NFR‑24a). The endpoint MUST NOT expose any sensitive information in its response body (a simple `{"status": "ok"}` or `OK` is sufficient).

---

## 5. Redundancy Inventory (what the refactor must eliminate)

This section is informative and drives §3 / §4. It documents the concrete duplication observed in the current codebase; it is not itself a requirement, but each item maps to a requirement above.

| Redundancy observed | Requirement removing it |
|---|---|
| `add_company.html`, `add_contract.html`, `add_person.html`, `add_undertaking.html` are byte‑for‑byte the same except for URL / heading | FR‑37, FR‑38, NFR‑5 |
| `edit_*.html` templates duplicate the `add_*.html` shape | FR‑37 |
| `all_*.html` list templates each redeclare an identical table skeleton with different columns | FR‑37, FR‑38 |
| Every `forms.py` uses `fields = "__all__"` and no widget/label customization | FR‑30 (serializers), plus a project‑wide crispy config (FR‑38) |
| `CompaniesView` / `CompanyView` etc. are the same pattern instantiated per entity via `BaseListView` / `BaseDetailView` with permission decorators built by inner closures | Replace with DRF viewsets + Django CBVs backed by shared services (NFR‑2) |
| Views detect API vs HTML by inspecting `Accept` / `Content-Type` and branch on `is_api_request()` | Split cleanly: DRF handles API; Django CBVs handle UI (FR‑29, FR‑30) |
| Sidebar links are hard‑coded in `master.html` | FR‑39 |
| Delete confirmations are inline `onclick` + a shared JS file | FR‑40 |
| Two separate URL files under `engagements/` for the two assignment types, each duplicating the include shape | Collapse using DRF routers and a single nested URL scheme (FR‑49) |
| Rename‑cycle migrations (`id` → `identifier` → `id`) in `companies`, `contracts`, `undertakings`, `people` | NFR‑20 |
| DRF installed but unused; `login_api` is a hand‑rolled JSON view marked `@csrf_exempt` | FR‑22, FR‑29 – FR‑35, NFR‑10 (replaced by DRF viewsets + HTTP Basic auth) |
| `Person.description` and `Person.location` declared with `blank=False, null=True` (contradictory) | Fixed as part of models cleanup under §3.1 (does not alter ERD types) |
| `Contract` has no `__str__` while other models do | Cleanup under §3.1 |
| `print(f"Permission: {permission_name}")` decorator left in `vendor_manager/views.py` | NFR‑28 |

---

## 6. Acceptance criteria

The refactor is considered complete when:

1. Every FR in §3 is demonstrated by a passing automated test.
2. Coverage thresholds in NFR‑17 are met (both overall ≥ 80% and diff coverage ≥ 80% on PRs).
3. `python manage.py check --deploy` reports zero warnings under the production settings profile.
4. There is exactly one `_list.html`, one `_detail.html`, one `_form.html` used by all standard entities; a `grep -c "extends \"master.html\"" **/templates/*.html` returns roughly the number of entity screens, not multiples of it.
5. Every action available in the UI is reproducible via a documented API call in the OpenAPI schema.
6. The sidebar navigation is generated from a single registry.
7. Migration history for each app is linear and free of rename cycles.
8. No template contains inline `style=`, `border=`, or hard‑coded `/entity/` URLs.
9. The dashboard renders correctly and produces identical numeric output to a captured baseline for a fixed test dataset AND passes the access‑control tests in NFR‑16 (a restricted user cannot see aggregates that would include entities they cannot access).
10. `ruff check`, `ruff format --check`, and `mypy --strict` all pass with zero errors on the entire project (NFR‑29, NFR‑30).
11. `mkdocs build --strict` succeeds and the MkDocs site is reachable at `/docs/` in a running container, with the API reference (Swagger UI) reachable at `/docs/api/` and linked from the MkDocs navigation (FR‑51, FR‑52).
12. The CD workflow builds the image on GitHub release, pushes it to Docker Hub under an immutable version tag, and deploys it to k3s via the reusable `deploy-to-k3s` action. The rolled‑out Deployment's `initContainer` runs `manage.py migrate --noinput` and the pod's `readinessProbe` at `/health/` reports ready before the workflow marks the release green (NFR‑24a, NFR‑39).

---

## 7. Resolved design questions

The following questions were raised during requirements review and have been resolved. They are kept here as a decision log; the resolutions are already reflected in §3 / §4 above.

- **OQ‑1 — Resolved.** `EngagementUndertakingAssignment.percentage` and `Leave.percentage` are represented as `0..1` in both the model and the API. No `0..100` conversion.
- **OQ‑2 — Resolved.** The OpenAPI schema and docs endpoints are publicly reachable in production but require authentication (username + password, per FR‑22 / FR‑35). They are not further gated to staff.
- **OQ‑3 — Resolved.** MSSQL support is dropped. Only PostgreSQL (production and Docker Compose dev) and SQLite (lightweight local dev / CI) are supported (NFR‑23).
- **OQ‑4 — Resolved.** UI delete flows use an intermediate confirmation page, not a JS `confirm()` prompt (FR‑40).
- **OQ‑5 — Resolved.** REST URLs follow standard conventions: nested paths for UI‑facing sub‑resources, optional flat filterable endpoints for reporting. Any URL in the current codebase that does not fit standard REST conventions is treated as a defect and MUST be corrected as part of the refactor (FR‑49).

---

## 8. Change log

- **v1** — initial draft, produced after codebase review; awaiting review sign‑off before implementation begins.
- **v1.1** — applied review clarifications: role library is now an implementation choice as long as the three roles are preserved (FR‑25); API auth switched to HTTP Basic with username + password as the required scheme, token auth dropped (FR‑22, NFR‑10); OpenAPI schema/docs are publicly reachable but auth‑gated in production (FR‑35, NFR‑11); MSSQL support removed, only PostgreSQL and SQLite are supported (NFR‑23, NFR‑24); UI delete flow now mandates an intermediate confirmation page (FR‑40); REST URL conventions clarified and "fix wrongly organized URLs" made a general rule (FR‑49); OQs 1–5 marked resolved (§7).
- **v1.2** — added CI, documentation, deployment, and dashboard requirements:
  - **CI pipeline** codified (NFR‑31): `ruff check`, `ruff format --check`, `mypy --strict`, `pytest`, `check --deploy`, `mkdocs build --strict` all gate every PR.
  - **Ruff replaces Black + isort** (NFR‑29); pre‑commit updated (NFR‑32).
  - **Strict type hints project‑wide** (NFR‑30): `mypy --strict` with `django-stubs` and `djangorestframework-stubs`; every function/method/class annotated. This supersedes the previous "incremental on new code" stance.
  - **Coverage** upgraded to two gates (NFR‑17): overall ≥ 80% AND diff coverage ≥ 80% on every PR.
  - **MkDocs documentation site** added as §3.10 (FR‑51–FR‑54) and served by the Django app at `/docs/`; the browsable API UI moves from `/api/v1/docs/` to `/docs/api/` so that `/docs/` is the single documentation entry point (FR‑35). README shrinks and redirects to MkDocs (NFR‑33).
  - **Continuous deployment** (NFR‑24a): release‑triggered, image pushed to a container registry, deployed to production with immutable version tags. **Initial draft incorrectly assumed the target was Docker Compose‑on‑VM with ghcr; see v1.2.1 for the correction.**
  - **Dashboard rework** (FR‑43–FR‑47): access control now enforced through the same `accessible_to(user)` selectors used by list endpoints; the dashboard is re‑implemented as a JSON API endpoint (`/api/v1/dashboards/summary/`) plus a minimal server‑rendered template using Plotly.js; `django-plotly-dash` is removed.
  - Renumbering: former FR‑46–FR‑48 shifted to FR‑48–FR‑50; former NFR‑33–NFR‑38 shifted to NFR‑34–NFR‑39; new NFR‑24a inserted; former NFR‑32 (README) is now NFR‑33.
- **v1.2.1 (this document)** — corrected the deployment section against the actual state of `main`, which had already migrated to k3s and release‑triggered CI/CD before the requirements review:
  - `NFR‑24a` rewritten: production target is **k3s** (Kubernetes), not Docker Compose‑on‑VM. Deployment goes through the reusable action `durczokj/vm/.github/actions/deploy-to-k3s@main`; the Kubernetes `Deployment` manifest lives at [deploy/k8s/deployment.yaml](https://github.com/durczokj/vendor_manager/blob/main/deploy/k8s/deployment.yaml) with `__IMAGE_TAG__` substitution and a migration `initContainer`. Kubernetes is explicitly IN scope.
  - Registry stays on **Docker Hub** (`durczokj/vendor-manager:<tag>`), matching the current pipeline. My earlier questionnaire answer that named ghcr is superseded.
  - `NFR‑24` rewritten to describe the actual local dev flow: `compose.yml` runs PostgreSQL only; the Django app runs on the host. Pure‑SQLite dev remains a supported second mode. The now‑unused `docker-compose.prod.yml` MUST be deleted.
  - Health‑check endpoint standardized on **`/health/`** (already in the k8s manifest and consistent with Django/DRF trailing‑slash conventions), not `/healthz`. `NFR‑11`, `NFR‑39`, and acceptance criterion 12 updated.
  - Acceptance criterion 12 rewritten to describe k3s rollout instead of docker‑compose deploy.
