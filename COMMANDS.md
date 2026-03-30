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

Create the local runtime env file from the committed template:

```bash
cp .env.example .env
```

Then edit `.env` for your local machine.
The Python services load variables from the repo-root `.env`, not `.env.example`.

Rate-limiting env note:

- local development can keep `RIFTHUB_RATE_LIMIT_BACKEND=memory`
- non-development environments should use `RIFTHUB_RATE_LIMIT_BACKEND=redis` with `RIFTHUB_REDIS_URL` set
- if the API is behind a trusted reverse proxy, set `RIFTHUB_TRUSTED_PROXY_IPS` so forwarded client IPs are trusted deliberately
- for local worker/feed-snapshot review, set `RIFTHUB_REDIS_URL=redis://127.0.0.1:6379/0`

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

Start local Postgres and Redis with Docker Compose:

```bash
npm run db:up
```

Stream Postgres and Redis logs:

```bash
npm run db:logs
```

Stop the local Docker services:

```bash
npm run db:down
```

Run the API test suite from the repository root:

```bash
npm run api:test
```

Import the approved ingestion source fixtures from the repository root:

```bash
npm run db:seed:sources
```

Apply the latest Alembic migration from the repository root:

```bash
npm run db:upgrade
```

Roll back the latest Alembic migration from the repository root:

```bash
npm run db:downgrade
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

Run Alembic directly:

```bash
uv run --package rifthub-api alembic -c apps/api/alembic.ini upgrade head
uv run --package rifthub-api alembic -c apps/api/alembic.ini downgrade -1
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
- Alembic config: `apps/api/alembic.ini`
- Alembic versions: `apps/api/alembic/versions`

## Notes

- Run all commands from the repository root unless the command says otherwise.
- The root `package.json` currently exposes `web:dev`, `api:dev`, `worker:dev`, `api:test`, `db:upgrade`, and `db:downgrade`.
- The root `package.json` currently exposes `web:dev`, `api:dev`, `worker:dev`, `api:test`, `db:up`, `db:down`, `db:logs`, `db:seed:feed`, `db:seed:sources`, `db:upgrade`, and `db:downgrade`.
- Linting and formatting commands are not documented here yet because they are not part of the current scaffold.
