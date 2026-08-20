# Developer Guide

Welcome. This section is written for **the people who maintain Vendor Manager**. If you
are looking for how to *use* the app, jump to the [User Guide](../user-guide/index.md).

## What lives here

- [Architecture](architecture.md) — how the codebase is organised, the UI/API split, and
  the services / selectors / managers layering.
- [Data model](data-model.md) — every entity in one place; links to the ERD.
- [Roles & permissions](roles-and-permissions.md) — the three roles and the exact
  permission matrix.
- [Coding conventions](coding-conventions.md) — the rules that keep the codebase
  reviewable: services vs. selectors vs. managers, thin views, docstrings, migrations,
  URL naming.
- [Testing](testing.md) — factories, permission-matrix tests, coverage gates.
- [Local dev](local-dev.md) — the two dev modes, seed data, verify loop.
- [Deployment](deployment.md) — the k3s CD pipeline, image tagging, rollback.

## Where to find things

- **Business rules** live in `<app>/services.py` (writes) and `<app>/selectors.py`
  (reads). Never in views.
- **Object-level access** is enforced by `<Entity>QuerySet.accessible_to(user)` in
  `<app>/managers.py`. Every view / viewset that returns queryset data calls it.
- **HTTP surface** — UI views in `<app>/views.py`, REST viewsets in `<app>/api.py`, both
  call into the same service.
- **URL naming** follows the DRF `<basename>-list` / `<basename>-detail` pattern per
  FR‑49 and FR‑50.

## Reference material

- [Requirements](../REQUIREMENTS.md) — the source of truth for every behavior. Cite the
  FR / NFR you satisfy in commit bodies.
- [Implementation plan](../IMPLEMENTATION_PLAN.md) — the phased refactor plan and its
  persisted progress checklist.

## Adding a new entity

Follow this checklist. Each step is described in [Coding conventions](coding-conventions.md).

1. Add the model in `<app>/models.py`. Enforce simple invariants in `clean()`.
2. Add or extend `<Entity>QuerySet` in `<app>/managers.py`, including `accessible_to()`.
3. Add write operations in `<app>/services.py`. Wrap multi-step writes in
   `transaction.atomic()`.
4. Add read-only computations in `<app>/selectors.py` (if any).
5. Add the serializer in `<app>/serializers.py` (explicit `fields = [...]`, per FR‑29).
6. Add the DRF `ModelViewSet` in `<app>/api.py`; register it on the router
   (`api/urls.py`).
7. Add the filter set in `<app>/filters.py`.
8. Add the Django form in `<app>/forms.py`, the CBVs in `<app>/views.py`, and the
   django-tables2 table in `<app>/tables.py`.
9. Register the URL patterns in `<app>/urls.py`.
10. Add a nav entry in `vendor_manager/navigation.py` (per FR‑39).
11. Add factories in `<app>/tests/factories.py` and tests for model / service /
    selector / permission (per NFR‑16).
