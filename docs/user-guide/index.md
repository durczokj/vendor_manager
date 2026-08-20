# User Guide

Welcome to Vendor Manager. This section is written for **people who use the app** to track
vendors, contracts, orders, people, engagements, undertakings, and leaves — not for the
developers who maintain it.

If you are a developer, jump to the [Developer Guide](../developer-guide/architecture.md) instead.

## What Vendor Manager is for

Vendor Manager keeps a single, auditable record of:

- **Companies** you buy services from and the **Contracts** you have with them
.
- **Orders** placed under those contracts, and the sequence of **Order versions** that track
  scope and price changes over time.
- **People** who work on your side of the fence — either your own staff or vendor
  consultants — and the **Engagements** that describe when and at what level of effort
  each person is working.
- **Undertakings** (initiatives / projects / work packages) and the **Cost centers** that
  own them.
- **Assignments** that connect an engagement to an undertaking or to a specific order
  version.
- **Leaves** that record time away and reduce a person's daily availability
.

Everything lives in one place so that the **dashboard** can tell
you, for any period, how much a set of engagements costs and how much of that cost is
covered by the order versions you have in place.

## The three roles at a glance

Every user has exactly one role. What you can see and do depends on it.

| Role | What they see | What they can change |
|---|---|---|
| **Admin** | Everything. | Everything. |
| **UndertakingManager** | The undertakings they manage plus every engagement, person, order and leave that touches those undertakings. | The same set. |
| **Person** | Their own person record, their engagements, their leaves, and the read-through supporting entities. | Very little — read-mostly. |

Read [Roles at a glance](roles.md) for the full picture and the exact rules.

## How to navigate this guide

Each workflow page has the same shape so you always know where to find what you need:

- **Purpose** — what the workflow is for, in one paragraph.
- **Who can do this** — which roles can perform it.
- **Screens** — the UI paths involved.
- **Happy path** — the numbered steps for the common case.
- **Common validation errors and how to fix them** — the messages you might see and what
  they mean.
- **Related workflows** — links to the pages that come before and after.

## Pages in this guide

- [Getting started](getting-started.md) — sign in, know where the navigation lives, sign out.
- [Roles at a glance](roles.md) — the three roles and what each can do.
- [Companies & contracts](companies-and-contracts.md) — record who you buy from and the
  contracts you hold.
- [Orders & versions](orders.md) — place orders and roll over versions as scope changes.
- [Undertakings & cost centers](undertakings.md) — describe the initiatives that consume
  engagements.
- [People & engagements](people-and-engagements.md) — record who works with you and at
  what level of effort.
- [Leaves](leaves.md) — record time away.
- [Dashboard](dashboard.md) — read cost and coverage aggregates.

!!! note "Screenshot pending"
    An overview screenshot of the sidebar + landing dashboard will be added here.
    Tracked as a P6.T5 follow-up.
