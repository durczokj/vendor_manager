# Testing

The test suite is the safety net for the phased refactor. Its rules are set by NFR‑16
through NFR‑19. This page is the day-to-day reference for authoring, running, and
gating tests.

## Toolchain

- **`pytest`** with `pytest-django` — test discovery, fixtures, parametrisation.
- **`pytest-cov`** — coverage measurement.
- **`diff-cover`** — diff-coverage gate on PRs.
- **`factory_boy`** — data-building for every test (per NFR‑19).
- **DRF `APIClient`** — HTTP-level tests for the REST API surface.
- Configuration lives in `[tool.pytest.ini_options]` in
  [`pyproject.toml`](https://github.com/durczokj/vendor_manager/blob/main/pyproject.toml).

## Layout

Each app owns its test tree. Factories are shared inside the app.

```
<app>/
  tests/
    __init__.py
    conftest.py            ← per-app fixtures
    factories.py           ← factory_boy factories (per NFR‑19)
    test_models.py         ← model invariants (FR‑12–FR‑17)
    test_services.py       ← service tests
    test_selectors.py      ← selector tests
    test_api.py            ← DRF APIClient tests per role
    test_permissions.py    ← object-level access matrix
```

The project-level `tests/` folder holds cross-app suites — most notably the permission
matrix (P7.T5).

## Factories

- Every test builds its data via `factory_boy` (per NFR‑19). Do not call
  `Model.objects.create(...)` in a test unless the factory does not exist yet — if that
  is the case, add the factory first.
- Factories produce coherent objects: `EngagementFactory` uses `PersonFactory` and
  `OrderFactory`; date fields default to sensible ranges; FTE defaults to a valid
  value.
- SQL-dump / JSON fixtures MUST NOT be used (per NFR‑19).

## Model invariants (P7.T2)

Every FR from FR‑12 through FR‑17 has at least one dedicated test method that either
asserts a `ValidationError` on invalid input or an accepted create on valid input. This
is what defends the model layer against regressions when logic moves between models,
services, and the database.

## Service tests (P7.T3)

Services own the multi-step business rules. Every service function is covered end to
end, including its **rollback path**. The canonical case is
`orders.services.create_new_order_version` (per FR‑18): a forced mid-transaction failure
MUST leave zero rows behind.

Cost calculations (per FR‑19) are covered by a JSON-snapshot test in
`engagements/tests/test_selectors.py`. The snapshot is checked into the repo; if the
snapshot changes, the test fails so the author must consciously accept the new
baseline.

## API tests per role (P7.T4)

For each viewset, one test class runs the six standard verbs (`list`, `retrieve`,
`create`, `update`, `partial_update`, `delete`) plus every custom `@action` from FR‑31,
with each of the three roles (`Admin`, `UndertakingManager`, `Person`). Both the allow
path and the deny path MUST be exercised — a role that should get 403 MUST have a test
that asserts 403.

Both Basic and session auth are exercised at least once per role somewhere in the
suite (per FR‑22).

## Permission matrix (P7.T5)

`tests/test_permission_matrix.py` iterates over every `(role, entity, verb)` triple and
asserts the expected HTTP status. Parametrised with `pytest.mark.parametrize`. Adding a
new entity requires exactly one new row in the parametrisation — the framework enforces
coverage.

The same test also asserts that
`Entity.objects.accessible_to(user)` matches the enumeration of `access_<entity>(user, e)`
across `Entity.objects.all()`, for each role. This is what keeps the ORM-filtered
`accessible_to` and the legacy object-level checkers in lockstep during the P2.T5
transition.

## Dashboard access-control (P7.T6)

A fixture builds two people with engagements. A `Person`-role user's dashboard payload
MUST include only their own aggregates — never anyone else's, even in totals. If a
future refactor accidentally bypasses `accessible_to(user)` in
`dashboards/selectors.py`, this test fails.

## Coverage gates

CI enforces two gates (per NFR‑17):

1. **Overall line coverage ≥ 80%** via `coverage report --fail-under=80`.
2. **Diff coverage ≥ 80%** on PRs via
   `diff-cover coverage.xml --compare-branch=origin/main --fail-under=80`.

The `services`, `selectors`, `permissions`, `api`, and `serializers` modules MUST hit
≥ 90% each (per P7's definition of done).

The diff-coverage gate lands as enforcing in P7.T7. Before then it is informational.

## Runtime target

The full suite MUST run against SQLite in under 60 seconds at the current entity count
(per NFR‑18). If a new suite blows the budget, split it into a faster unit-level tier
and a slower integration tier — do not weaken the gate.

## Local verify loop

```bash
DJANGO_DEBUG=true DJANGO_SECRET_KEY=dev DATABASE_ENGINE=sqlite pytest --cov
```

For the full pre-push loop (ruff, mypy, deploy check, mkdocs) see
[Coding conventions](coding-conventions.md#verify-loop).

## Related pages

- [Coding conventions](coding-conventions.md) — where each layer lives.
- [Roles & permissions](roles-and-permissions.md) — the matrix the tests assert
  against.
- [Local dev](local-dev.md) — how to run the suite locally.
