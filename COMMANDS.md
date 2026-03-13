# RiftHub Commands

This file documents the commands currently available in the Phase 1 scaffold.
It only includes commands that exist in the repository today.

## Prerequisites

- Node.js 22+
- npm 11+
- Python 3.12+
- `uv`

## Install Dependencies

Install web dependencies from the repository root:

```bash
npm install
```

Install Python workspace dependencies from the repository root:

```bash
uv sync --all-packages
```

## Run The Apps

Start the Next.js web app from the repository root:

```bash
npm run web:dev
```

Start the FastAPI app from the repository root:

```bash
npm run api:dev
```

Start the worker from the repository root:

```bash
npm run worker:dev
```

## Validation Commands

Run the API test scaffold:

```bash
uv run --package rifthub-api pytest apps/api/tests
```

Check the API health route once the API is running:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"service":"api","status":"ok","environment":"development"}
```

Run the worker directly without the root npm script:

```bash
uv run --package rifthub-worker rifthub-worker
```

## Direct Package Entrypoints

Run the API package entrypoint directly:

```bash
uv run --package rifthub-api rifthub-api
```

Run a one-off Python command in the API package environment:

```bash
uv run --package rifthub-api python -c "from fastapi.testclient import TestClient; from rifthub_api.main import app; print(TestClient(app).get('/health').json())"
```

Run the worker package entrypoint directly:

```bash
uv run --package rifthub-worker rifthub-worker
```

## Useful Paths

- Web app: `apps/web`
- API app: `apps/api`
- Worker app: `apps/worker`
- Shared backend package: `packages/backend`
- Seed data: `scripts/seed-data/approved_sources.dev.json`

## Notes

- Run all commands from the repository root unless the command says otherwise.
- The root `package.json` currently exposes only `web:dev`, `api:dev`, and `worker:dev`.
- Linting, formatting, database, and migration commands are not documented here because they are not part of the current scaffold yet.
