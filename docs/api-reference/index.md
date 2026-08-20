# API Reference

Vendor Manager exposes a REST API at `/api/v1/`. This section is written for people
integrating with the API — typically the seeding script (`scripts/populate.py`), the
smoke-test tooling, or an external system.

## What lives here

- [Using the API](using-the-api.md) — authentication, pagination, filtering, custom
  actions, nested endpoints, error shape.
- **Swagger UI** at [/docs/api/](/docs/api/) — the interactive schema browser. Use it
  to explore endpoints, inspect request/response shapes, and try calls live.
- **OpenAPI schema** at `/api/v1/schema/` — the machine-readable YAML for code
  generation.

## Design principles

- **UI and API share business logic.** Both surfaces call the same `services.py` and
  `selectors.py`. No behavior differs between them.
- **Object-level access is enforced uniformly.** Every viewset's `get_queryset` returns
  `Entity.objects.accessible_to(self.request.user)`.
- **Explicit serializer fields.** Every serializer declares `fields = [...]` — no
  `__all__`. Adding a field to a model does not silently expose it.
- **Standard URL naming.** DRF `basename-list` / `basename-detail` / `basename-<action>`
. No custom URL conf.

## Versioning

The current version is `v1`, mounted at `/api/v1/`. Breaking changes will introduce
`/api/v2/` alongside — the two versions coexist until deprecation is announced.

## Related pages

- [Architecture](../developer-guide/architecture.md) — how the API relates to the UI
  surface.
- [Roles & permissions](../developer-guide/roles-and-permissions.md) — the matrix that
  gates every endpoint.
- [Data model](../developer-guide/data-model.md) — the entities the API surfaces.
