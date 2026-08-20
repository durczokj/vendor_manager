# Vendor Manager

**Vendor Manager** is a Django 5.1 application for tracking vendors, contracts, orders,
people, engagements, undertakings, and leaves. It provides:

- A **server-rendered UI** — tabular lists, plain forms, and detail pages with a minimalist
  "database-like" aesthetic.
- A **REST API** — full feature parity with the UI, authenticated via HTTP Basic Auth and
  documented through an OpenAPI/Swagger schema.

## Quick links

| Destination | URL |
|---|---|
| Application UI | `/` |
| REST API root | `/api/v1/` |
| OpenAPI schema | `/api/v1/schema/` |
| API reference (Swagger UI) | `/docs/api/` |
| Documentation (this site) | `/docs/` |

## About this site

This documentation site is built with [MkDocs](https://www.mkdocs.org/) using the
[Material theme](https://squidfunk.github.io/mkdocs-material/). It is served by the
Django application itself at `/docs/` and rebuilt as part of every CI run and production
Docker image build (see [Deployment](developer-guide/deployment.md)).

Use the navigation on the left to explore:

- **[Getting started](user-guide/getting-started.md)** — run the app locally in under five minutes.
- **[Architecture](developer-guide/architecture.md)** — how the codebase is structured, the UI/API split,
  and the services/selectors pattern.
- **[Data model](ERD.md)** — entity-relationship diagram for all tracked entities.
- **[Roles & permissions](developer-guide/roles-and-permissions.md)** — the three roles and their permission
  matrices.
- **[Local dev](developer-guide/local-dev.md)** — full local development guide.
- **[Deployment](developer-guide/deployment.md)** — the k3s continuous-deployment pipeline.
- **[Requirements](REQUIREMENTS.md)** — full functional and non-functional requirements.
