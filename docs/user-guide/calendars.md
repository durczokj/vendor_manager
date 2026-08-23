# Calendars

A **calendar** describes which days a person is expected to work — the recurring
weekly pattern (e.g. Monday–Friday) plus the public holidays that apply where they
work. Assigning a calendar to a person makes the app treat their non‑working days as
free time: dashboard costs drop to zero on those days (per FR‑19) and the absence
matrix on `/leaves/` shades them red (per FR‑61).

## Purpose

Keep cost and availability numbers honest. Without a calendar, the app assumes every
day is a working day. With one, weekends and holidays stop dragging cost figures up.

## Who can do this

- **Admin.** Full control — creates and edits weekly patterns, holiday calendars, and
  calendars in the Django admin (`/admin/`), and assigns any calendar to any person.
- **UndertakingManager.** Assigns existing calendars to the people whose engagements
  sit under their undertakings. Cannot create new patterns, holiday sources, or
  calendars — that is admin work.
- **Person.** No access.

## The four building blocks

The model has four small pieces (per FR‑55):

- **Weekly pattern.** A recurring weekly rhythm stored as a 7‑bit mask: Monday to
  Sunday. Example: *Mon–Fri* means Saturday and Sunday are free every week.
- **Holiday calendar.** A named source of public holidays, identified by an
  ISO‑3166 country code (optionally a subdivision such as a US state). Holidays are
  resolved on demand; you don't have to enter each date.
- **Calendar.** A named bundle of one weekly pattern + one holiday calendar. This is
  the unit you assign to people. Example: *Poland Mon–Fri* = Mon–Fri pattern + Poland
  holidays.
- **Calendar assignment.** A dated link between a person and a calendar. It has a
  start date and an optional end date. A person may have several assignments over
  time (e.g. a relocation from Poland to Germany), but they must not overlap.

## Screens

- **Assign a calendar to a person.** Open the person's detail page
  (`/people/<code>/`). Scroll to the **Calendar Assignments** block. Add / Edit /
  Delete controls live in that block (per FR‑60).
- **Maintain calendars, weekly patterns, and holiday calendars.** Admin only — via
  `/admin/calendars/` in the Django admin site.

There is no top‑level "Calendars" tab in the sidebar. Assignments are managed where
people are managed, on the person's detail page.

## Happy path — assign a calendar to a person

1. Ask an admin (once) to make sure the calendar you need exists — e.g. *Poland
   Mon–Fri*, *Germany Mon–Fri*, *UK Mon–Fri*.
2. Open the person's detail page (`/people/<code>/`).
3. Scroll to **Calendar Assignments** and click **Add**.
4. Pick the **calendar**.
5. Set the **start date**. Leave the **end date** empty for open‑ended (currently in
   effect); set an end date if you know when this arrangement stops.
6. Save. The next dashboard refresh and the next visit to `/leaves/` will reflect the
   new working days.

## Happy path — edit or delete an assignment

1. Open the person's detail page (`/people/<code>/`).
2. In the **Calendar Assignments** block, click **Edit** or **Delete** on the row.
3. For deletes, confirm on the intermediate page (per FR‑40).

## Rules the system enforces

| Rule | Meaning |
|---|---|
| `end_date >= start_date` | You can't end a period before it starts. |
| No two assignments overlap for the same person | A person is either on one calendar or another on any given day, never both. Open‑ended assignments (no end date) are treated as running forever until you set an end. |
| `access_person` | UndertakingManagers can only add / edit / delete assignments for people they can already access. |

## Common validation errors and how to fix them

| Message | What it means | How to fix |
|---|---|---|
| "end_date cannot be before start_date." | Trivial ordering rule. | Fix the end date. |
| "Overlaps with assignment N (…)." | A previous assignment already covers part of the range. | Set an end date on the previous assignment first, or narrow the new range. |
| "You do not have permission to assign a calendar to this person." | You're an UndertakingManager and the target person is not in your scope. | Ask an admin, or an UndertakingManager who does manage that person's undertaking. |

## Related workflows

- Alongside: [Leaves](leaves.md) — the absence matrix uses your calendar assignments
  to paint free days red.
- Downstream: [Dashboard](dashboard.md) — cost per day drops to zero on free days.
- Admin only: creating the underlying weekly patterns, holiday calendars, and
  calendars is done from the Django admin site.
