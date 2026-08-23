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

- **Leaves list & absence matrix.** `/leaves/` — the leaves list, followed by the
  absence matrix for planning (see below).
- **Create leave.** `/leaves/create/`
- **Delete leave.** `/leaves/<id>/delete/` (intermediate confirmation, per FR‑40)

!!! note "Screenshot pending"
    A screenshot of the leaves list and the absence matrix will be added here.
    Tracked as a P6.T5 follow-up.

## Happy path — record a leave

1. Open `/leaves/` and click **Add leave**.
2. Pick the **person** the leave applies to.
3. Set the **start date** and **end date** — the system enforces
   `start_date ≤ end_date`.
4. Set the **percentage** — a decimal between `0` and `1` (per FR‑17). Use `1.0` for a
   full day off, `0.5` for a half day, and so on.
5. Optional: add a reason / note field if your deployment shows one.
6. Save. The leave is recorded and immediately subtracted from the person's daily
   availability in dashboard calculations.

## Reading the absence matrix

The `/leaves/` page includes an **absence matrix** for planning (per FR‑61). Filter by
undertaking to see, day by day, how much of your team is out.

- **Blue‑ish shaded cells** encode cumulative leave percentage — the darker the cell,
  the more of the day is unavailable.
- **Red cells** mark **free days** for that person — weekends and public holidays as
  defined by their assigned calendar (per FR‑57). A leave on a free day still renders
  as a leave cell (leaves take precedence).

Free days come from each person's [Calendar assignment](calendars.md). If a person has
no calendar assigned, no red cells will appear for them; the matrix falls back to
assuming every day is a working day.

## Happy path — delete a leave

1. Open `/leaves/` and find the leave in the list or absence matrix.
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
- Alongside: [Calendars](calendars.md) — free days on the absence matrix come from
  the person's calendar assignment.
- Downstream: [Dashboard](dashboard.md) — leaves lower daily availability, which lowers
  the person's daily cost on the leave days (per FR‑19).
