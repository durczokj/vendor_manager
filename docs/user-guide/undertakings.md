# Undertakings & cost centers

An `Undertaking` (per FR‑6) is a **unit of work you own** — a project, an initiative, a
programme, a workstream. It has a manager, a set of engagements assigned to it, and it
rolls up into a `CostCenter` (per FR‑9) for reporting.

## Purpose

Describe the internal side of the org chart so that every engagement can be attributed
to the initiative that consumes it, and every cost can be summed by cost center.

## Who can do this

Admin (full). UndertakingManager can edit the undertakings they manage. Person is
read-only.

## Screens

- **Undertaking list.** `/undertakings/`
- **Undertaking detail.** `/undertakings/<id>/`
- **Create undertaking.** `/undertakings/create/`
- **Edit undertaking.** `/undertakings/<id>/update/`
- **Delete undertaking.** `/undertakings/<id>/delete/` (intermediate confirmation, per FR‑40)

!!! note "Screenshot pending"
    A screenshot of the undertaking list will be added here. Tracked as a P6.T5 follow-up.

## Happy path — create an undertaking

1. Open `/undertakings/` and click **Add undertaking**.
2. Fill in the name and pick the **cost center** it rolls up into.
3. Pick the **manager** — a `Person` who will be granted UndertakingManager access to
   this undertaking (per FR‑27). The person must already exist; if not, add them first
   through [People & engagements](people-and-engagements.md).
4. Save. The undertaking is now on the list, and the chosen manager can see and edit it.

## Happy path — assign a manager

Whether you're creating a new undertaking or re-assigning an existing one, the
**Manager** field is what controls who has UndertakingManager access.

1. Open the undertaking's detail page at `/undertakings/<id>/`.
2. Click **Edit**.
3. Change the **Manager** field to the new person.
4. Save. The former manager loses access; the new manager gains it (per FR‑27, FR‑28).

## Happy path — cost centers

Cost centers are usually seeded by Finance or Operations up front. When you need a new
one:

1. Open the cost-center admin (developer-facing — most deployments do not expose cost
   center CRUD to end users).
2. Add the new cost center.
3. Return to the undertaking form and select it from the dropdown.

If your deployment exposes cost centers as a top-level list, the workflow mirrors the
undertaking one.

## Common validation errors and how to fix them

| Message | What it means | How to fix |
|---|---|---|
| "Manager is required." | Every undertaking must have exactly one manager. | Pick a person from the dropdown. |
| "Cannot delete: this undertaking still has engagement assignments." | An engagement is still assigned to this undertaking (per FR‑10, FR‑14). | Open each assignment from the detail page and remove it, then retry the delete. |
| "Cost center is required." | Undertakings must roll up into a cost center. | Pick one from the dropdown; if none exist, ask Finance to seed one. |

## Related workflows

- Before: [People & engagements](people-and-engagements.md) — the manager must exist as a
  person first.
- After: [People & engagements](people-and-engagements.md) — assign engagements to this
  undertaking through the assignment sub-form (per FR‑10, FR‑14).
- Downstream: [Dashboard](dashboard.md) — filter aggregates by cost center or
  undertaking.
