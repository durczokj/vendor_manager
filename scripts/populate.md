# `scripts/populate.py` — Coverage Reference

This document lists every entity the script creates and every API endpoint it
exercises.  Use it to verify coverage without reading the script.

## Dataset created (with `--seed 42`)

| Entity | Count | Notes |
|--------|-------|-------|
| `CostCenter` | 2 | IDs 1–2 |
| `Person` (managers) | 6 | IDs `M-001` … `M-006` |
| `Undertaking` | 6 | One per manager; alternates between the 2 cost centers |
| `Company` | 3 | IDs 1–3 |
| `Contract` | 5 | 3 initial + 2 extra created for the clone-latest action |
| `Order` | 3 | IDs 1–3; one per company |
| `OrderVersion` | 5 | 3 initial + 2 cloned via `clone-latest` |
| `Person` (consultants) | 30 | IDs `P-001` … `P-030` |
| `Engagement` | 30 | One per consultant |
| `EngagementOrderVersionAssignment` | 30 | One per engagement; cycled over the 3 initial versions |
| `EngagementUndertakingAssignment` | 30 | One per engagement; cycled over the 6 undertakings |
| `Leave` | 3 | For consultants `P-001`, `P-002`, `P-003` |
| **Total `Person`** | **36** | 6 managers + 30 consultants |

## Endpoints exercised

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/health/` | Pre-flight connectivity check |
| `GET` | `/api/v1/cost-centers/` | List (during reset) |
| `POST` | `/api/v1/cost-centers/` | Create |
| `DELETE` | `/api/v1/cost-centers/{id}/` | Delete (during reset) |
| `GET` | `/api/v1/people/` | List (during reset) |
| `POST` | `/api/v1/people/` | Create managers + consultants |
| `DELETE` | `/api/v1/people/{id}/` | Delete (during reset) |
| `GET` | `/api/v1/undertakings/` | List (during reset) |
| `POST` | `/api/v1/undertakings/` | Create |
| `DELETE` | `/api/v1/undertakings/{id}/` | Delete (during reset) |
| `GET` | `/api/v1/companies/` | List (during reset) |
| `POST` | `/api/v1/companies/` | Create |
| `DELETE` | `/api/v1/companies/{id}/` | Delete (during reset) |
| `GET` | `/api/v1/contracts/` | List (during reset) |
| `POST` | `/api/v1/contracts/` | Create initial + clone contracts |
| `DELETE` | `/api/v1/contracts/{id}/` | Delete (during reset) |
| `GET` | `/api/v1/orders/` | List (during reset) |
| `POST` | `/api/v1/orders/` | Create |
| `DELETE` | `/api/v1/orders/{id}/` | Delete (during reset) |
| `GET` | `/api/v1/order-versions/` | List (during reset) |
| `POST` | `/api/v1/order-versions/` | Create initial versions |
| `DELETE` | `/api/v1/order-versions/{id}/` | Delete (during reset) |
| `POST` | `/api/v1/orders/{id}/versions/clone-latest/` | Clone latest version (FR-31) |
| `GET` | `/api/v1/engagements/` | List (during reset) |
| `POST` | `/api/v1/engagements/` | Create |
| `DELETE` | `/api/v1/engagements/{id}/` | Delete (during reset) |
| `GET` | `/api/v1/engagement-order-version-assignments/` | List (during reset) |
| `POST` | `/api/v1/engagement-order-version-assignments/` | Create |
| `DELETE` | `/api/v1/engagement-order-version-assignments/{id}/` | Delete (during reset) |
| `GET` | `/api/v1/engagement-undertaking-assignments/` | List (during reset) |
| `POST` | `/api/v1/engagement-undertaking-assignments/` | Create |
| `DELETE` | `/api/v1/engagement-undertaking-assignments/{id}/` | Delete (during reset) |
| `GET` | `/api/v1/leaves/` | List (during reset) |
| `POST` | `/api/v1/leaves/` | Create |
| `DELETE` | `/api/v1/leaves/{id}/` | Delete (during reset) |

## Satisfies

- `FR-29`, `FR-30`, `FR-31`, `FR-32`, `FR-33`, `FR-34`, `FR-35`, `NFR-16`
