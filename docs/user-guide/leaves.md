# Leaves

A `Leave` (per FR‑11) is a **time-bounded absence** for a person — vacation, sickness,
parental leave, sabbatical. Leaves reduce the person's daily availability, so cost
calculations on the dashboard (per FR‑19) treat those days differently.

## Purpose

Keep an accurate picture of when someone is not billable, so the dashboard's cost and
coverage numbers reflect reality.

## Who can do this

Admin (full). UndertakingManager can record leaves for the people whose engagements sit
under their undertakings. Person can read their own leaves.

## Screens

- **Leaves list.** `/leaves/` — includes the calendar / matrix view for planning.
- **Create leave.** `/leaves/create/`
- **Delete leave.** `/leaves/<id>/delete/` (intermediate confirmation, per FR‑40)

!!! note "Screenshot pending"
    A screenshot of the leaves list with the calendar / matrix view will be added here.
    Tracked as a P6.T5 follow-up.

## Happy path — record a leave

1. Open `/leaves/` and click **Add leave**.
2. Pick the **person** the leave applies to.
3. Set the **start date** and **end date** — the system enforces
   `start_date ≤ end_date`.
4. Set the **percentage** — a decimal between `0` and `1` (per FR‑17). Use `1.0` for a
   full day off, `0.5` for a half day, and so on.
5. Optional: add a reason / note field if your deployment shows one.
6. Save. The leave is added to the calendar and immediately subtracted from the
   person's daily availability in dashboard calculations.

## Reading the leave matrix

The `/leaves/` page includes a matrix / calendar view for planning. Filter by
undertaking to see, day by day, how much of your team is out. Cells are shaded by
cumulative leave percentage so you can spot conflicts at a glance.

## Happy path — delete a leave

1. Open `/leaves/` and find the leave in the list or calendar.
2. Click **Delete** on the row.
3. Confirm on the intermediate page (per FR‑40).

Leaves have no dependents, so deletion always succeeds once you confirm.

## Common validation errors and how to fix them

| Message | What it means | How to fix |
|---|---|---|
| "Percentage must be between 0 and 1." | The percentage is outside the allowed range (per FR‑17). | Enter a decimal between 0 and 1. |
| "End date must be on or after start date." | Trivial ordering rule. | Fix the end date. |
| "Person is required." | Every leave must belong to a person. | Pick a person from the dropdown. |

## Related workflows

- Before: [People & engagements](people-and-engagements.md) — the person and their
  engagement must exist for the leave to have an effect on cost.
- Downstream: [Dashboard](dashboard.md) — leaves lower daily availability, which lowers
  the person's daily cost on the leave days (per FR‑19).
