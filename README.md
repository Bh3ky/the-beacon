# RiftHub

Phase 1 sets up the repository as a small monorepo with:

- `apps/web`: Next.js App Router frontend
- `apps/api`: FastAPI service entrypoint
- `apps/worker`: background worker entrypoint
- `packages/backend`: shared Python backend package
- `scripts/seed-data`: development fixture data

## Prerequisites

- Node.js 22+
- npm 11+
- Python 3.12+
- `uv`

## Getting Started

Install JavaScript dependencies:

```bash
npm install
```

Install Python workspace dependencies:

```bash
uv sync --all-packages
```

Create a local runtime env file before starting services:

```bash
cp .env.example .env
```

Then edit `.env` for your local machine.
The Python services load `.env` at runtime, not `.env.example`.

Run the three scaffolded runtimes from the repo root:

```bash
npm run web:dev
npm run api:dev
npm run worker:dev
```

The API exposes `GET /health` once started.

## Database Workflow

Phase 2 adds PostgreSQL, SQLAlchemy, and Alembic.
Local Python runtime settings now load from the repo-root `.env`.

Start local Postgres with Docker:

```bash
npm run db:up
```

Watch Postgres logs:

```bash
npm run db:logs
```

Run the API test suite:

```bash
npm run api:test
```

Apply the latest database migration:

```bash
npm run db:upgrade
```

Roll back one migration:

```bash
npm run db:downgrade
```

Stop the Docker services when done:

```bash
npm run db:down
```
