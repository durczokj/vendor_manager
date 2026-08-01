# Deployment

Vendor Manager runs on **k3s** (lightweight Kubernetes) and is deployed automatically
on every GitHub release via a GitHub Actions CD workflow.

## CI / CD overview

```
Pull request → CI workflow (lint, type-check, test, mkdocs build)
                     │
                     ▼
main branch  ──────────────────────────────────────────────
                     │
           GitHub release published
                     │
                     ▼
              CD workflow
           ┌──────────────┐
           │ Build image  │  docker build → durczokj/vendor-manager:<tag>
           │ Push to Hub  │  docker push  → Docker Hub
           └──────┬───────┘
                  │
           ┌──────▼───────────────────────────┐
           │ deploy-to-k3s composite action   │
           │  (durczokj/vm/.github/actions/   │
           │   deploy-to-k3s@main)            │
           └──────────────────────────────────┘
```

## Docker image

The production image is built from [`Dockerfile`](https://github.com/durczokj/vendor_manager/blob/main/Dockerfile)
and tagged with an **immutable version tag** (the release tag name, e.g. `v1.2.3`).
The `:latest` tag is never used by any deployment manifest.

The image is pushed to Docker Hub under `durczokj/vendor-manager:<tag>`.

## Kubernetes deployment

The Kubernetes `Deployment` manifest lives at
[`deploy/k8s/deployment.yaml`](https://github.com/durczokj/vendor_manager/blob/main/deploy/k8s/deployment.yaml).

Key aspects of the manifest:

- **`__IMAGE_TAG__` placeholder** — replaced by the reusable deploy action with the
  resolved release tag before `kubectl apply`.
- **`initContainer`** — runs `python manage.py migrate --noinput` before the app
  container starts, so database migrations are applied atomically on every deploy.
- **`readinessProbe` / `livenessProbe`** — both target the unauthenticated `/health/`
  endpoint (HTTP 200 + DB ping). The rollout does not mark the deployment green until
  the probe passes.
- **`resources`** — CPU: 50 m–500 m; memory: 128 Mi–512 Mi.

Cluster-side resources (`Service`, `Ingress`, `ConfigMap`, `Secret`, `Namespace`) are
managed by the reusable action and its supporting repository; they are **not** duplicated
here.

## Triggering a deployment

### Automatic (on release)

1. Draft and publish a GitHub release with a version tag (e.g. `v1.2.3`).
2. The CD workflow (`release: published`) triggers automatically.
3. Monitor progress in the **Actions** tab of the repository.

### Manual (workflow dispatch)

```
GitHub → Actions → CD workflow → Run workflow → enter tag name → Run
```

This dispatches the same pipeline for an explicit tag — useful for re-deploying a
known-good version after a rollback.

## Rollback

Re-dispatch the CD workflow (`workflow_dispatch`) with the previous known-good tag.
The deploy action will roll out the older image; once the `readinessProbe` at `/health/`
passes, the rollout is complete.

## Static files & docs

WhiteNoise (`CompressedManifestStaticFilesStorage`) serves all static files.
The MkDocs documentation site is built into the image at build time (`mkdocs build --strict`)
and served by the Django app at `/docs/`.

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | Yes | Django secret key (min 50 chars in production) |
| `DJANGO_ALLOWED_HOSTS` | Yes | Comma-separated list of allowed hostnames |
| `DJANGO_DEBUG` | No | Set to `false` (default) in production |
| `DATABASE_ENGINE` | No | `postgresql` (default) or `sqlite` |
| `DATABASE_NAME` | Postgres only | Database name |
| `DATABASE_USER` | Postgres only | Database user |
| `DATABASE_PASSWORD` | Postgres only | Database password |
| `DATABASE_HOST` | Postgres only | Database host |
| `DATABASE_PORT` | Postgres only | Database port |
| `FORCE_SCRIPT_NAME` | No | Sub-path prefix (e.g. `/app`) for reverse-proxy setups |
