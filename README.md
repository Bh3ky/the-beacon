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

Run the three scaffolded runtimes from the repo root:

```bash
npm run web:dev
npm run api:dev
npm run worker:dev
```

The API exposes `GET /health` once started.
