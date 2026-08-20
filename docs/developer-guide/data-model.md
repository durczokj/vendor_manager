# Data model

Vendor Manager tracks eleven entities. Their relationships are frozen for the current
refactor cycle — the ERD is the source of truth and MUST NOT be modified (per
`REQUIREMENTS.md` §2.1).

## Entity-relationship diagram

The full ERD, with every field and relationship, is checked in at
[docs/ERD.md](../ERD.md). Open it for the diagram, the field-level detail, and the
domain glossary.

## Entity index

Follow the code links for the model definition.

| Entity | App | Model |
|---|---|---|
| Company | `companies` | `companies.models.Company` |
| Contract | `contracts` | `contracts.models.Contract` |
| Order | `orders` | `orders.models.Order` |
| OrderVersion | `orders` | `orders.models.OrderVersion` |
| Undertaking | `undertakings` | `undertakings.models.Undertaking` |
| CostCenter | `undertakings` | `undertakings.models.CostCenter` |
| Person | `people` | `people.models.Person` |
| Engagement | `engagements` | `engagements.models.Engagement` |
| EngagementUndertakingAssignment | `engagements` | `engagements.models.EngagementUndertakingAssignment` |
| EngagementOrderVersionAssignment | `engagements` | `engagements.models.EngagementOrderVersionAssignment` |
| Leave | `leaves` | `leaves.models.Leave` |

## Invariants

The temporal and range invariants are enforced at three layers:

- **Model layer** — `clean()` / `full_clean()` for single-model rules.
- **Service layer** — cross-model rules and multi-step writes.
- **Database layer** — unique-together constraints, non-null defaults.

Any change to an invariant location MUST NOT weaken an existing rule; the aggregate
invariant surface is verified by the P7 test suite.

## Migration policy

- Migrations are **additive**. Never rewrite an applied migration.
- Squashed initials (`0001_initial_squashed_*.py`) landed in P1.T2 and MUST be treated as
  the historical base.
- Both SQLite and PostgreSQL are supported; every migration MUST pass
  `migrate` on both. Any use of `RunPython` MUST provide `reverse_code`.

## Related pages

- [Architecture](architecture.md) — how these entities are exposed through the two
  surfaces.
- [Coding conventions](coding-conventions.md) — the rules for editing models and
  authoring migrations.
- [Roles & permissions](roles-and-permissions.md) — object-level access per entity.
