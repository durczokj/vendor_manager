# Getting started

This page walks you through signing in, finding your way around, and signing out. It
does **not** cover installing the app — for that, developers should read
[Local dev](../developer-guide/local-dev.md).

## Purpose

Get you from a fresh browser tab to a working session, oriented enough to reach any
workflow in the User Guide.

## Who can do this

Anyone with an account: Admin, UndertakingManager, or Person (per FR‑25).

## Screens

- `/accounts/login/` — the sign-in page (per FR‑21).
- `/` — the dashboard, which is what you land on after signing in (per FR‑43).
- `/accounts/logout/` — the sign-out endpoint.

## Happy path

### 1. Sign in

1. Open Vendor Manager in your browser. If you are not signed in, you will be redirected
   to `/accounts/login/`.
2. Enter your username and password. If your account has not been linked to a person
   record, sign-in is rejected with a readable error (per FR‑23) — contact your
   administrator to have your `Person` record linked.
3. On success, you land on the dashboard at `/`.

!!! note "Screenshot pending"
    A screenshot of the sign-in screen will be added here. Tracked as a P6.T5 follow-up.

### 2. Orient yourself in the sidebar

The left sidebar is generated from the [navigation registry](../developer-guide/architecture.md)
and only shows entries you have permission to open (per FR‑39). Common entries:

- **Companies** — `/companies/`
- **Contracts** — `/contracts/`
- **Orders** — `/orders/`
- **Undertakings** — `/undertakings/`
- **People** — `/people/`
- **Engagements** — `/engagements/`
- **Leaves** — `/leaves/`

If an entry is missing, your role does not grant access to that entity (per FR‑26,
FR‑27). Ask an Admin to widen your role if you need it.

!!! note "Screenshot pending"
    A screenshot of the sidebar navigation will be added here. Tracked as a P6.T5 follow-up.

### 3. Change your password

Password management uses Django's built-in flow. Ask your administrator for the current
path — self-service password change is available if the administrator has enabled the
`/accounts/password_change/` view for your deployment.

### 4. Sign out

Follow the "Sign out" link in the sidebar. Your session is invalidated immediately.

## Common validation errors and how to fix them

| Message | What it means | How to fix |
|---|---|---|
| "Please enter a correct username and password." | The credentials were not recognised. | Retry, or ask an administrator to reset your password. |
| "Your account is not linked to a person record." | Your user has no linked `Person` (per FR‑23). | Ask an administrator to create or link a person record before you sign in again. |
| Redirect loop to `/accounts/login/` after a successful sign-in. | Session cookies are being blocked by your browser. | Allow cookies for the app's domain and retry. |

## Related workflows

- Next up: [Roles at a glance](roles.md) — understand what you are allowed to do before
  you start clicking around.
- If you are looking for setup instructions, see the developer-facing
  [Local dev](../developer-guide/local-dev.md).
