# Using the API

This page is the operational reference for the `/api/v1/` surface. For the interactive
schema browser see [/docs/api/](/docs/api/).

## Authentication

Two authentication mechanisms are supported:

| Mechanism | When to use |
|---|---|
| **HTTP Basic Auth** | Scripts, integrations, CI. The default for `scripts/populate.py`. |
| **Session Auth** | Browser-based use of the API (Swagger UI while logged in). |

Every endpoint EXCEPT `/health/` requires authentication. An
unauthenticated request returns `401 Unauthorized`.

### Basic Auth

```bash
curl -u admin:admin https://vendor-manager.example.com/api/v1/companies/
```

### Session Auth + CSRF

Session-authenticated `POST`, `PUT`, `PATCH`, `DELETE` requests MUST send the CSRF
token in the `X-CSRFToken` header, matching the `csrftoken` cookie. Read requests do
not need it.

## Pagination

Every list endpoint is paginated by `PageNumberPagination`:

- Default page size: **50**.
- Max page size: **200**.
- Client override: `?page=2&page_size=100`.

Response envelope:

```json
{
    "count": 137,
    "next": "https://.../api/v1/companies/?page=3",
    "previous": "https://.../api/v1/companies/?page=1",
    "results": [ ... ]
}
```

## Filtering, search, and ordering

Every list endpoint enables three backends: `DjangoFilterBackend`, `SearchFilter`,
`OrderingFilter`.

- **Field filters** — declared per viewset in `<app>/filters.py`. Example:
  `GET /api/v1/companies/?is_active=true`.
- **Search** — `?search=<term>` matches the fields listed in the viewset's
  `search_fields`.
- **Ordering** — `?ordering=name` or `?ordering=-created_at`. Restricted to fields
  listed in the viewset's `ordering_fields`.

## Custom actions

Custom `@action` endpoints extend the standard six verbs:

| Endpoint | Method | Purpose |
|---|---|---|
| `POST /api/v1/orders/{id}/versions/clone-latest/` | POST | Clone the latest `OrderVersion` for this order. |
| `GET /api/v1/engagements/{id}/costs/` | GET | Cost breakdown for the engagement. |
| `GET /api/v1/engagements/{id}/cost-coverage/` | GET | Order-version coverage of the engagement's dated cost span. |
| `GET /api/v1/people/{id}/assignments/` | GET | All active `EngagementUndertakingAssignment` rows for the person. |

Every custom action honours the same `accessible_to(user)` gate as its parent viewset.

## Nested endpoints

Nested routes surface many-to-many assignment tables under their parent:

| Endpoint | Purpose |
|---|---|
| `/api/v1/engagements/{pk}/undertaking-assignments/` | CRUD for `EngagementUndertakingAssignment`. |
| `/api/v1/engagements/{pk}/order-version-assignments/` | CRUD for `EngagementOrderVersionAssignment`. |

The nested router is `drf-nested-routers` — nested URLs use the parent's `basename`
prefix.

## Error shape

DRF's default JSON error shape is used throughout. Example:

```json
{
    "detail": "You do not have permission to perform this action."
}
```

Validation errors are keyed by field:

```json
{
    "start_date": ["End date must be after start date."],
    "non_field_errors": ["Engagement overlaps existing assignment."]
}
```

Cross-model invariants raise `ValidationError` in the service layer and are surfaced
as `400 Bad Request` with the same shape.

## Rate limits and quotas

None currently enforced. Fair-use expected. If you are running a bulk
import, throttle client-side and prefer batching where the API supports it (e.g.
`/versions/clone-latest/` for order versions).

## Working example: `scripts/populate.py`

The seeding script is the canonical usage example. It:

1. Authenticates with HTTP Basic.
2. Lists every entity with pagination.
3. Creates a coherent dataset seeded by an integer (`--seed`).
4. Uses `--reset` to purge existing rows first.

See [Local dev — Populating sample data](../developer-guide/local-dev.md#populating-sample-data)
for the invocation, and [`scripts/populate.md`](https://github.com/durczokj/vendor_manager/blob/main/scripts/populate.md)
for the endpoint coverage matrix.

## Related pages

- [Architecture](../developer-guide/architecture.md) — where API code lives in the
  codebase.
- [Roles & permissions](../developer-guide/roles-and-permissions.md) — the exact matrix
  every viewset enforces.
- [Testing](../developer-guide/testing.md) — how the API surface is regression-tested.
