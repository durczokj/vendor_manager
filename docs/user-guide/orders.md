# Orders & versions

An `Order` (per FR‑4) is the commercial agreement that funds work at your organisation.
An `OrderVersion` (per FR‑5) is a **time-bounded revision** of that order — the price,
scope, or contract changes, so you close the old version and open a new one. The
Vendor Manager keeps every version so you can always see who was working under which
terms on any given day.

## Purpose

Record the flow of work from a vendor's perspective: contract → order → sequence of
versions → engagements assigned to each version.

## Who can do this

Admin (full). UndertakingManager can maintain the orders and versions that fund the
undertakings they manage. Person is read-only.

## Screens

- **Order list.** `/orders/`
- **Order detail.** `/orders/<id>/` — shows all versions of the order.
- **Create order.** `/orders/create/`
- **Edit order.** `/orders/<id>/update/`
- **Delete order.** `/orders/<id>/delete/` (intermediate confirmation, per FR‑40)
- **Order version list.** `/order_versions/`
- **Order version detail.** `/order_versions/<id>/`
- **Create order version.** `/order_versions/create/`
- **Edit order version.** `/order_versions/<id>/update/`

!!! note "Screenshot pending"
    A screenshot of an order detail page with its version timeline will be added here.
    Tracked as a P6.T5 follow-up.

## Happy path — create an order and its first version

1. Open `/orders/` and click **Add order**.
2. Pick the **company** and enter an order name/identifier.
3. Save. You are on the new order's detail page.
4. In the **Versions** related block, click **Add order version**.
5. Pick the **contract** that governs this version, the **start date**, and the
   **end date**. Optional: daily rate, availability, and any commercial fields.
6. Save. This is now the **first (and currently only) version** of the order.

## Happy path — clone the latest version (roll over)

This is the FR‑18 workflow — when scope or price changes, you don't edit the old version,
you clone it and shorten the old one to match. The system runs the whole operation as a
single transaction (per FR‑18, NFR‑1): either the new version is created cleanly, or
nothing changes.

1. Open the order's detail page at `/orders/<id>/`.
2. Click **Clone latest version**.
3. In the dialog, pick:
   - the **new contract** (usually the same, sometimes a fresh contract),
   - the **new start date** — this MUST be later than the current latest version's start
     date (per FR‑16),
   - the **new end date** — MUST be on or after the start date (per FR‑16),
   - whether to **copy engagement assignments** from the previous version (default
     **on**).
4. Click **Clone**. Behind the scenes:
   - The previous version's end date is shortened to the day before the new start date
     (so the two versions abut with no gap and no overlap — FR‑16).
   - The new version is created.
   - Any existing engagement–order-version assignments are copied over (if you left the
     checkbox on).
5. You are redirected to the new version's detail page.

!!! note "Screenshot pending"
    A screenshot of the "clone latest version" dialog will be added here.
    Tracked as a P6.T5 follow-up.

## How versions chain start and end dates (FR‑16)

- A version's `start_date` must be on or before its `end_date`.
- Consecutive versions of the same order must **not overlap**.
- Consecutive versions of the same order must **not leave a gap**.

If you break any of these rules — usually by moving a start date backwards — Vendor
Manager rejects the save with a readable error message.

## Common validation errors and how to fix them

| Message | What it means | How to fix |
|---|---|---|
| "This contract is already used by another order version." | A contract can back only one order version at a time. | Pick a different contract, or shorten the other version. |
| "Start date must be later than the previous version's start date." | Cloning tried to open a new version at or before the current one (per FR‑16). | Pick a new start date after the previous version's start. |
| "End date must be on or after start date." | Trivial ordering rule (per FR‑16). | Fix the end date. |
| "Cannot delete: this order still has engagements assigned to a version." | Assignments on a version block deletion. | Remove assignments first, or delete versions in reverse order. |

## Related workflows

- Before this: [Companies & contracts](companies-and-contracts.md) — you need a
  company and a contract to place an order.
- After this: [People & engagements](people-and-engagements.md) — engagements are what
  actually consume order-version capacity.
- Downstream: [Dashboard](dashboard.md) — order-version coverage is what drives the
  "covered vs. uncovered" split.
