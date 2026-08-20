# Data model

Vendor Manager tracks eleven entities. Their relationships are frozen for the current
refactor cycle — the ERD is the source of truth and MUST NOT be modified (per
`REQUIREMENTS.md` §2.1).

## Entity-relationship diagram

The full ERD, with every field and relationship, is checked in at
[docs/ERD.md](../ERD.md). Open it for the diagram, the field-level detail, and the
domain glossary.

## Entity index

Each row cites the FR that governs the entity's behavior. Follow the code links for the
model definition.

| Entity | FR | App | Model |
|---|---|---|---|
| Company | FR‑1 | `companies` | `companies.models.Company` |
| Contract | FR‑2 | `contracts` | `contracts.models.Contract` |
| Order | FR‑4 | `orders` | `orders.models.Order` |
| OrderVersion | FR‑5 | `orders` | `orders.models.OrderVersion` |
| Undertaking | FR‑6 | `undertakings` | `undertakings.models.Undertaking` |
| CostCenter | FR‑9 | `undertakings` | `undertakings.models.CostCenter` |
| Person | FR‑7 | `people` | `people.models.Person` |
| Engagement | FR‑8 | `engagements` | `engagements.models.Engagement` |
| EngagementUndertakingAssignment | FR‑10 | `engagements` | `engagements.models.EngagementUndertakingAssignment` |
| EngagementOrderVersionAssignment | FR‑13 | `engagements` | `engagements.models.EngagementOrderVersionAssignment` |
| Leave | FR‑11 | `leaves` | `leaves.models.Leave` |

## Invariants

The temporal and range invariants are documented in `REQUIREMENTS.md` §3.2 (FR‑12 through
FR‑17). They are enforced at three layers:

- **Model layer** — `clean()` / `full_clean()` for single-model rules (FR‑13, FR‑14,
  FR‑16, FR‑17).
- **Service layer** — cross-model rules and multi-step writes (FR‑15, FR‑18).
- **Database layer** — unique-together constraints, non-null defaults (per FR‑12,
  Redundancy Inventory).

Any change to an invariant location MUST NOT weaken an existing rule; the aggregate
invariant surface is verified by the P7 test suite (per NFR‑16).

## Migration policy

- Migrations are **additive**. Never rewrite an applied migration.
- Squashed initials (`0001_initial_squashed_*.py`) landed in P1.T2 and MUST be treated as
  the historical base.
- Both SQLite and PostgreSQL are supported (per NFR‑21); every migration MUST pass
  `migrate` on both. Any use of `RunPython` MUST provide `reverse_code` (per NFR‑22).

## Related pages

- [Architecture](architecture.md) — how these entities are exposed through the two
  surfaces.
- [Coding conventions](coding-conventions.md) — the rules for editing models and
  authoring migrations.
- [Roles & permissions](roles-and-permissions.md) — object-level access per entity.
