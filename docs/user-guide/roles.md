# Roles at a glance

Vendor Manager assigns every user to **exactly one** of three roles. Your role decides
which screens appear in the sidebar and which records you can read or change (per FR‑25,
FR‑26, FR‑27, FR‑28).

## Purpose

Answer, before you attempt a task, "am I even allowed to do this?"

## Who can do this

Everyone — this page is informational.

## The three roles

### Admin

- **Sees.** Every entity in the system.
- **Changes.** Every entity in the system.
- **Typical user.** Operations lead, HR partner, finance controller.

### UndertakingManager

- **Sees.** Every undertaking they manage, and everything reachable from those
  undertakings — the engagements assigned to them, the people behind those engagements,
  the orders and versions that fund them, and the leaves of the people involved.
- **Changes.** The same set (per FR‑27).
- **Typical user.** Project or programme manager owning a delivery workstream.

### Person

- **Sees.** Their own person record, their engagements, their leaves, and the entities
  read-through those (their orders, their contracts, their undertakings) (per FR‑28).
- **Changes.** Almost nothing — read-mostly.
- **Typical user.** A consultant or staff member checking their own assignments.

## What each role can do, per entity

The table below is a business-facing summary. The developer-facing detail lives in
[Roles & permissions](../developer-guide/roles-and-permissions.md).

| Entity | Admin | UndertakingManager | Person |
|---|:---:|:---:|:---:|
| Company (FR‑1) | R/W | R (through orders) | R (through orders) |
| Contract (FR‑2, FR‑3) | R/W | R | R |
| Order (FR‑4) | R/W | R/W (their scope) | R (through engagements) |
| Order version (FR‑5) | R/W | R/W (their scope) | R (through engagements) |
| Undertaking (FR‑6) | R/W | R/W (theirs) | R (through engagements) |
| Cost center (FR‑9) | R/W | R | R |
| Person (FR‑7) | R/W | R (their people) | R (self) |
| Engagement (FR‑8) | R/W | R/W (their people) | R (own) |
| EngagementUndertakingAssignment (FR‑10) | R/W | R/W (theirs) | R (own) |
| EngagementOrderVersionAssignment (FR‑13) | R/W | R/W (theirs) | R (own) |
| Leave (FR‑11) | R/W | R | R (own) |

**R** = can read. **R/W** = can read and change. Blank cells mean no access; you will
not see the sidebar entry either.

!!! note "Screenshot pending"
    A screenshot of the role-matrix reference card will be added here.
    Tracked as a P6.T5 follow-up.

## What if I need access I don't have?

Ask an Admin to widen your role or to grant you management of a specific undertaking.
Roles are enforced at every layer (UI, API, and the database queryset itself — per
NFR‑7), so no workaround exists on your side.

## Related workflows

- [Getting started](getting-started.md) — sign in and see what your role reveals.
- [Companies & contracts](companies-and-contracts.md) — the first workflow most Admins
  perform.
- [People & engagements](people-and-engagements.md) — the most common workflow for
  UndertakingManagers.
