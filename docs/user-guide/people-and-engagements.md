# People & engagements

A `Person` (per FR‑7) is anyone who does work in the system — your own staff or a vendor
consultant. An `Engagement` (per FR‑8) is a **time-bounded work arrangement** for that
person: it says when they start, when they end, at what level of effort (FTE), and — via
assignments — which undertakings and order versions they contribute to.

## Purpose

Answer, for any period, "who is working on what, and under whose funding?"

## Who can do this

Admin (full). UndertakingManager can create people and engagements that will be assigned
to the undertakings they manage. Person can read their own record and engagements.

## Screens

- **People list.** `/people/`
- **Person detail.** `/people/<id>/`
- **Create person.** `/people/create/`
- **Edit person.** `/people/<id>/update/`
- **Delete person.** `/people/<id>/delete/`
- **Engagements list.** `/engagements/`
- **Engagement detail.** `/engagements/<id>/`
- **Create engagement.** `/engagements/create/`
- **Edit engagement.** `/engagements/<id>/update/`
- **Delete engagement.** `/engagements/<id>/delete/` (intermediate confirmation, per FR‑40)

!!! note "Screenshot pending"
    A screenshot of a person detail page with the engagements block will be added here.
    Tracked as a P6.T5 follow-up.

## Happy path — create a person

1. Open `/people/` and click **Add person**.
2. Fill in the person's identifier, name, and optional description / location fields.
3. Optionally link a Django user account so the person can sign in.
4. Save. You are on the person's detail page, ready to add engagements.

## Happy path — create an engagement

1. From the person's detail page, click **Add engagement** in the **Engagements** related
   block. Alternatively, open `/engagements/create/` directly.
2. Pick the **person** (auto-filled if you came from the person page).
3. Pick the **order** the engagement is under (per FR‑8).
4. Set the **start date** and **end date**. The system enforces
   `start_date ≤ end_date`.
5. Set the **FTE** — a decimal between `0` and `1` (per FR‑12). `1.0` is full-time,
   `0.5` is half-time, and so on.
6. Save. The engagement now appears on the person's detail page and in the top-level
   `/engagements/` list.

## Happy path — assign the engagement to an undertaking

Once the engagement exists, tell the system which undertaking it feeds. This is what
lets the dashboard aggregate by undertaking (per FR‑10, FR‑14).

1. Open the engagement's detail page at `/engagements/<id>/`.
2. In the **Undertaking assignments** related block, click **Add assignment**.
3. Pick the **undertaking** and enter a **start date**, **end date**, and **percentage**
   (a decimal between 0 and 1) representing how much of this engagement is allocated to
   that undertaking.
4. Save.

Vendor Manager enforces (per FR‑14):

- The assignment's date range MUST fit inside the engagement's date range.
- Two assignments of the same `(engagement, undertaking)` pair MUST NOT overlap.

You can add multiple undertaking assignments to the same engagement (an engagement is
often split across several undertakings), as long as no two overlap for the same
undertaking.

## Happy path — assign the engagement to an order version

This is what makes the engagement "funded". A person's cost is only counted as covered
for the days on which an order-version assignment exists (per FR‑19).

1. Open the engagement's detail page at `/engagements/<id>/`.
2. In the **Order-version assignments** related block, click **Add assignment**.
3. Pick the **order version**. Because of FR‑13, the version must belong to the same
   order as the engagement — the dropdown filters to matching versions only.
4. Enter dates and percentage.
5. Save.

!!! note "Screenshot pending"
    A screenshot of the assignment form will be added here. Tracked as a P6.T5 follow-up.

## What happens when you edit engagement dates (FR‑15)

If you shorten or move an engagement's `start_date` / `end_date`, existing
`EngagementUndertakingAssignment` records that fall outside the new range are
**automatically trimmed** to stay inside it (per FR‑15). You will see the adjusted dates
on the detail page after saving.

Assignments that would become empty (end before start) are refused with a validation
error rather than silently deleted, so you notice the conflict.

## Common validation errors and how to fix them

| Message | What it means | How to fix |
|---|---|---|
| "FTE must be between 0 and 1." | The FTE field is outside the allowed range (per FR‑12). | Enter a decimal value between 0 and 1. |
| "Order version does not belong to this engagement's order." | You picked a version from a different order (per FR‑13). | Pick a version whose order matches the engagement's order. |
| "Undertaking assignment must fall inside the engagement's date range." | The assignment starts before or ends after the engagement (per FR‑14). | Move the assignment dates, or extend the engagement first. |
| "Undertaking assignment overlaps another for the same undertaking." | Two assignments of the same `(engagement, undertaking)` overlap (per FR‑14). | Close one before opening the next, or edit one to end earlier. |
| "Cannot delete: this engagement has assignments." | Assignments block deletion of the parent engagement. | Remove all assignments first, or delete via the confirmation page in a single step. |

## Related workflows

- Before: [Orders & versions](orders.md) — you need an order (with at least one version)
  to hang an engagement off.
- Before: [Undertakings & cost centers](undertakings.md) — you need an undertaking to
  assign the engagement to.
- After: [Leaves](leaves.md) — record time away that reduces the person's daily
  availability.
- Downstream: [Dashboard](dashboard.md) — this is what the summary chart aggregates.
