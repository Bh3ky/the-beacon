# Phase 1 Foundation Plan

## Purpose

This plan defines the first codebase setup pass for `RiftHub`.

It is intentionally limited to repository structure and runtime skeletons.
It does **not** include product features, domain models, auth flows, or ingestion logic yet.

## Preconditions

Before implementation starts:

- rename the root folder from `the-beacon` to `rifthub`
- keep the docs folder in place
- treat this phase as scaffolding only, not feature delivery

## Decisions Locked For This Setup

- product name: `RiftHub`
- frontend package manager: `npm`
- frontend scaffold method: `npx create-next-app`
- Python toolchain: `uv`
- Python structure: shared backend package plus thin app entrypoints
- keep web UI dependencies minimal for now
- move the temporary approved-source JSON into the new monorepo structure

## Target Repository Shape

```text
rifthub/
  apps/
    web/
    api/
    worker/
  packages/
    backend/
  scripts/
    seed-data/
  infra/
  docs/
  .github/
  .env.example
  .gitignore
  README.md
  package.json
  pyproject.toml
```

## Implementation Scope

### 1. Root workspace setup

Create the base monorepo folders:

- `apps/`
- `packages/`
- `scripts/`
- `infra/`
- `.github/`

Create root workspace files:

- `package.json`
- `pyproject.toml`
- `.env.example`

Goals:

- npm workspaces manage the frontend app
- uv workspace manages the Python app projects and shared backend package
- root documentation reflects the monorepo structure

### 2. Frontend scaffold

Create `apps/web` as a plain Next.js App Router project using `npx create-next-app`.

Include:

- TypeScript
- App Router
- Tailwind CSS

Do not include yet:

- shadcn/ui
- product routes beyond the minimal scaffold
- API integration code
- Zustand or other app state libraries

Expected result:

- `apps/web` starts locally
- default page renders
- workspace scripts can run the web app from root

### 3. Shared Python backend package

Create `packages/backend` as the shared Python package for backend logic.

Recommended import name:

- `rifthub_backend`

Initial contents should be minimal:

- package metadata
- shared config module
- shared logging module
- base package layout only

Do not add domain services yet.

### 4. API app skeleton

Create `apps/api` as a thin FastAPI entrypoint project.

Initial scope:

- app startup
- config bootstrap
- health route
- basic test scaffold
- imports from `packages/backend`

Do not add yet:

- auth
- database models
- Alembic revisions
- service-domain logic

### 5. Worker app skeleton

Create `apps/worker` as a thin worker runtime project.

Initial scope:

- worker entrypoint
- one no-op runner or job
- logging bootstrap
- imports from `packages/backend`

Do not add yet:

- polling logic
- ranking jobs
- queue integration

### 6. Seed-data relocation

Move:

- `backend/dev/approved_sources.dev.json`

To:

- `scripts/seed-data/approved_sources.dev.json`

Reason:

- it is development fixture data, not runtime backend code

After the move:

- remove the old top-level `backend/` directory if it is empty

### 7. Minimal root scripts

Add root-level scripts only if they improve developer flow immediately.

Reasonable first scripts:

- web dev start
- API dev start
- worker dev start

Avoid overbuilding orchestration in this phase.

## Validation Checkpoints

The scaffold pass is complete only if all of these work:

1. The monorepo folder structure matches the planned layout.
2. `apps/web` starts and serves the default Next.js page.
3. `apps/api` starts and `GET /health` responds.
4. `apps/worker` starts and logs a basic startup message.
5. The shared Python package can be imported by both API and worker apps.
6. The development source seed file exists in `scripts/seed-data/`.

## Explicit Non-Goals

This phase should not drift into:

- auth/session implementation
- CSRF implementation
- DB modeling
- migrations
- feed endpoints
- submission flows
- moderation actions
- ingestion workers
- frontend product UI

## Recommended Execution Order

```text
rename repo folder
→ create root workspace files and folders
→ scaffold apps/web
→ create packages/backend
→ create apps/api
→ create apps/worker
→ move seed data
→ verify all three runtimes start
```

## Notes For The Next Phase

Once this foundation pass is complete, the next implementation slice should be:

```text
shared config
→ database connectivity
→ base models and migrations
→ API health plus core schema plumbing
```
