# Dashboard

The dashboard at `/` is the **summary view** of the whole system. It
combines engagements, order versions, and leaves into two headline numbers per period:
**cost** and **cost coverage**.

## Purpose

Answer, at a glance, "how much are we spending, and how much of that is funded?"

## Who can do this

Everyone. What you see is filtered by your role — a `Person` sees only their own
aggregates, an `UndertakingManager` sees the undertakings they manage, and an `Admin`
sees the whole system. The filter is applied server-side, so no user
ever sees an aggregate that includes entities they cannot access.

## Screens

- **Dashboard.** `/` — the landing page after sign-in.

!!! note "Screenshot pending"
    A screenshot of the dashboard chart and underlying table will be added here.
    Tracked as a P6.T5 follow-up.

## The four filter dimensions

You can pivot the dashboard by:

1. **Class** — which type of entity to group by (person, undertaking, cost center,
   engagement, order).
2. **Granularity** — how to bucket time (day, week, month, quarter).
3. **Date range** — from and to dates.
4. **Entity selection** — narrow to a specific set within the chosen class (for
   example, only two undertakings you own).

The dropdowns are populated from an endpoint that itself enforces
`accessible_to(user)` — so, for example, an UndertakingManager only sees
their own undertakings in the "entity" dropdown.

## What "cost" means

For each person, on each day inside the selected range:

- **Base cost** = `daily_rate × fte × availability`.
- **Availability** is reduced by any overlapping `Leave` percentage.
- The result is summed across the group and bucketed by the chosen granularity.

## What "cost coverage" means

For each day and each person, the system checks which order-version assignments are
active. The **covered share** is the sum of those assignments' percentages, capped at
100%. Any remainder is labelled **unassigned** and shown in a distinct colour.

- If covered = 100% for a day, the day is **fully funded**.
- If covered = 60% for a day, 60% of that day's cost is **covered** and 40% is
  **unassigned**.
- If you see "unassigned" bars, that's usually a sign that an order version expired
  before the next was created) or that an
  engagement was created without an order-version assignment
  ([People & engagements](people-and-engagements.md)).

## Happy path — read the chart

1. Open `/`.
2. Pick a **class** — usually "undertaking" for a manager or "person" for HR.
3. Pick a **granularity** — usually "month".
4. Pick a **date range** — often the current quarter.
5. (Optional) narrow the **entity selection**.
6. Read:
   - The **chart** shows total cost per bucket, split into "covered" and "unassigned".
   - The **table** below shows the underlying numbers, one row per entity per bucket.

## Common questions

**Why don't I see person X in the dropdown?**
Because your role does not grant you access to that person. Ask an
Admin to widen your role if you need it.

**Why does the total look lower than I expect for a specific week?**
Check whether:

- People have leave in that week — leaves reduce availability, which
  reduces cost.
- The order version supporting an engagement expired mid-week — days after
  the expiration count as "unassigned" and the covered total drops.
- Engagement date ranges have been trimmed by an edit.

**Why does my dashboard look empty?**
Either your role has access to nothing, or the current filters exclude all data. Try
widening the date range and clearing the entity selection.

## Related workflows

- Upstream: [People & engagements](people-and-engagements.md) — engagements drive
  cost.
- Upstream: [Orders & versions](orders.md) — versions drive coverage.
- Upstream: [Leaves](leaves.md) — leaves reduce daily cost.
- Reference: [Roles at a glance](roles.md) — explains why you may see less than a
  colleague.
