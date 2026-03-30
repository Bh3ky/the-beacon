# Phase 5 To 8 Test And Code Review Guide

Date: `2026-03-24`
Status: `ready to follow`

## Purpose

Use this guide to manually review the implementation work completed after Phase 4 and before starting Phase 9.

It covers:

1. focused automated test runs
2. manual product checks
3. code-review order by phase
4. slice-by-slice file review targets

This is the follow-on review guide for:

- Phase 5 ranking
- Phase 6 worker system
- Phase 7 moderation
- Phase 8 ingestion

It complements:

- [PHASE5_RANKING_PLAN.md](/Users/telasi/Developer/RiftHub/docs/agent-review/PHASE5_RANKING_PLAN.md)
- [PHASE6_WORKER_PLAN.md](/Users/telasi/Developer/RiftHub/docs/agent-review/PHASE6_WORKER_PLAN.md)
- [PHASE7_MODERATION_PLAN.md](/Users/telasi/Developer/RiftHub/docs/agent-review/PHASE7_MODERATION_PLAN.md)
- [PHASE8_INGESTION_PLAN.md](/Users/telasi/Developer/RiftHub/docs/agent-review/PHASE8_INGESTION_PLAN.md)
- [DEVELOPMENT_TEST_CHECKPOINTS.md](/Users/telasi/Developer/RiftHub/docs/agent-review/DEVELOPMENT_TEST_CHECKPOINTS.md)
- [INGESTION_SOURCE_FORMAT.md](/Users/telasi/Developer/RiftHub/docs/agent-review/INGESTION_SOURCE_FORMAT.md)
- [OPERATIONS_ROLES.md](/Users/telasi/Developer/RiftHub/docs/agent-review/OPERATIONS_ROLES.md)

## Review Goal

Before entering Phase 9, confirm that:

- ranking behavior is intentional and stable
- worker jobs are understandable and safe
- moderation is role-protected and auditable
- ingestion is review-safe and operationally coherent

## Preconditions

From the repo root:

```bash
npm install
uv sync --all-packages
cp .env.example .env
```

Make sure your local runtime is pointed at the correct database and Redis settings.

For manual review sessions, start:

```bash
npm run db:up
npm run db:upgrade
npm run api:dev
npm run web:dev
```

Optional:

- keep `RIFTHUB_VERIFICATION_DELIVERY_MODE=log` for local auth/testing
- use the role setup flow from [OPERATIONS_ROLES.md](/Users/telasi/Developer/RiftHub/docs/agent-review/OPERATIONS_ROLES.md) if you want full moderator/admin UI checks

## Recommended Review Order

Follow this order:

1. Phase 5 ranking
2. Phase 6 worker system
3. Phase 7 moderation
4. Phase 8 ingestion

That preserves the actual dependency chain in the codebase.

## Shared Fast Checks

Run these once before starting the phase-by-phase review:

```bash
curl http://127.0.0.1:8000/health
```

```bash
./node_modules/.bin/tsc -p apps/web/tsconfig.json --noEmit
```

Expected:

- API health returns `ok`
- frontend typecheck passes

If either of those fails, stop before deeper review.

---

## Phase 5 Review

### What Phase 5 Covers

- post ranking alignment
- comment ranking behavior
- deterministic feed ordering
- jobs separation from the main `top` feed
- rank-sensitive creation/vote write paths

### Focused Automated Tests

From the repo root:

```bash
uv run --package rifthub-api pytest \
  apps/api/tests/test_reads.py \
  apps/api/tests/test_reads_helpers.py \
  apps/api/tests/test_creation_helpers.py \
  apps/api/tests/test_creation_routes.py \
  apps/api/tests/test_voting_helpers.py \
  apps/api/tests/test_voting_routes.py -q
```

Optional confidence pass:

```bash
uv run --package rifthub-api pytest apps/api/tests -q
```

### Manual Product Checks

Open:

- `/`
- `/new`
- `/ask`
- `/show`
- `/jobs`
- one real `/post/[id]/[slug]`

Verify:

- jobs do not appear on `/`
- jobs do appear on `/jobs`
- ranked feeds are stable across refreshes
- comment sort links behave intentionally:
  - `top`
  - `new`
  - `old`
- a fresh voted post is not buried at zero visibility
- equal-looking posts do not shuffle unpredictably on refresh

### Code Review Order

#### Slice 1: ranking invariants

Read:

- [voting.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/voting.py)
- [reads.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/reads.py)

Verify:

- post rank formula is centralized
- comment rank formula is intentional
- jobs are excluded from ranked top feed paths

#### Slice 2: creation and write-path alignment

Read:

- [creation.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/creation.py)
- [posts.py](/Users/telasi/Developer/RiftHub/apps/api/src/rifthub_api/routes/posts.py)

Verify:

- post creation initializes rank
- comment creation refreshes parent post rank
- no duplicate hidden ranking logic exists outside the backend package

#### Slice 3: frontend comment ordering

Read:

- [comments.ts](/Users/telasi/Developer/RiftHub/apps/web/lib/comments.ts)
- [page.tsx](/Users/telasi/Developer/RiftHub/apps/web/app/post/[id]/[slug]/page.tsx)

Verify:

- comment sibling ordering for `top` is explicit
- frontend tree building does not accidentally undo backend intent

#### Slice 4: test coverage

Read:

- [test_reads_helpers.py](/Users/telasi/Developer/RiftHub/apps/api/tests/test_reads_helpers.py)
- [test_creation_helpers.py](/Users/telasi/Developer/RiftHub/apps/api/tests/test_creation_helpers.py)
- [test_voting_helpers.py](/Users/telasi/Developer/RiftHub/apps/api/tests/test_voting_helpers.py)

Verify:

- tie-breakers are covered
- self-vote restrictions are covered
- jobs feed separation is covered

---

## Phase 6 Review

### What Phase 6 Covers

- worker runtime and scheduling
- ranking refresh
- feed snapshots
- reconciliation
- job expiry
- duplicate-execution control

### Focused Automated Tests

```bash
uv run --package rifthub-worker pytest apps/worker/tests -q
```

```bash
uv run --package rifthub-api pytest \
  apps/api/tests/test_ranking_refresh.py \
  apps/api/tests/test_feed_snapshots.py \
  apps/api/tests/test_reconciliation.py \
  apps/api/tests/test_job_expiry.py -q
```

### Manual Runtime Checks

If your local env has a usable Redis URL configured, run:

```bash
npm run worker:dev
```

Verify from logs:

- worker starts cleanly
- jobs register and schedule cleanly
- no immediate lock or import errors occur
- jobs log structured success/failure summaries

If Redis is not available locally, rely on the focused worker tests and code review instead of forcing a broken manual run.

### Code Review Order

#### Slice 1: runtime shell

Read:

- [main.py](/Users/telasi/Developer/RiftHub/apps/worker/src/rifthub_worker/main.py)
- [scheduler.py](/Users/telasi/Developer/RiftHub/apps/worker/src/rifthub_worker/runners/scheduler.py)

Verify:

- scheduling is explicit
- job registration is centralized
- runtime is thin

#### Slice 2: ranking refresh

Read:

- [refresh_post_scores.py](/Users/telasi/Developer/RiftHub/apps/worker/src/rifthub_worker/jobs/refresh_post_scores.py)
- [ranking_refresh.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/ranking_refresh.py)

Verify:

- shared ranking logic is reused
- worker does not invent its own score formula

#### Slice 3: snapshots and reconciliation

Read:

- [refresh_feed_snapshots.py](/Users/telasi/Developer/RiftHub/apps/worker/src/rifthub_worker/jobs/refresh_feed_snapshots.py)
- [feed_snapshots.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/feed_snapshots.py)
- [reconcile_vote_counts.py](/Users/telasi/Developer/RiftHub/apps/worker/src/rifthub_worker/jobs/reconcile_vote_counts.py)
- [reconciliation.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/reconciliation.py)

Verify:

- Redis snapshot payloads are deterministic and small
- reconciliation repairs canonical counters rather than guessing

#### Slice 4: expiry policy

Read:

- [expire_job_posts.py](/Users/telasi/Developer/RiftHub/apps/worker/src/rifthub_worker/jobs/expire_job_posts.py)
- [job_expiry.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/job_expiry.py)

Verify:

- expiry stays separate from moderation state
- 30-day bounds are enforced consistently

#### Slice 5: locks and safety

Read:

- [locks.py](/Users/telasi/Developer/RiftHub/apps/worker/src/rifthub_worker/runners/locks.py)
- [test_locks.py](/Users/telasi/Developer/RiftHub/apps/worker/tests/test_locks.py)

Verify:

- lease ownership is explicit
- releases are owner-checked
- overlapping runs skip rather than double-execute

---

## Phase 7 Review

### What Phase 7 Covers

- flag review queue
- moderator/admin role enforcement
- moderation audit actions
- moderation web UI

### Focused Automated Tests

```bash
uv run --package rifthub-api pytest \
  apps/api/tests/test_flags.py \
  apps/api/tests/test_moderation.py \
  apps/api/tests/test_user_roles.py -q
```

### Manual Product Checks

Use the setup in [OPERATIONS_ROLES.md](/Users/telasi/Developer/RiftHub/docs/agent-review/OPERATIONS_ROLES.md).

Verify with three real accounts:

- one moderator
- one admin
- one normal user

Check:

- normal user cannot access `/moderation`
- moderator can access `/moderation`
- admin can access `/moderation`
- moderator can dismiss flags and use normal moderation actions
- admin can ban users
- moderator cannot ban users

### Code Review Order

#### Slice 1: authz boundary

Read:

- [dependencies.py](/Users/telasi/Developer/RiftHub/apps/api/src/rifthub_api/dependencies.py)

Verify:

- moderator/admin checks are centralized
- admin-only paths are explicit

#### Slice 2: moderation service

Read:

- [moderation.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/moderation.py)
- [models/moderation.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/models/moderation.py)

Verify:

- enforcement and audit happen together
- destructive actions do not bypass audit rows

#### Slice 3: moderation routes

Read:

- [routes/moderation.py](/Users/telasi/Developer/RiftHub/apps/api/src/rifthub_api/routes/moderation.py)
- [schemas.py](/Users/telasi/Developer/RiftHub/apps/api/src/rifthub_api/schemas.py)

Verify:

- routes stay thin
- response payloads are explicit
- CSRF is enforced on mutating moderation routes

#### Slice 4: web review surface

Read:

- [moderation-dashboard.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/moderation/moderation-dashboard.tsx)
- [page.tsx](/Users/telasi/Developer/RiftHub/apps/web/app/moderation/page.tsx)
- [header-auth.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/auth/header-auth.tsx)

Verify:

- moderator affordances do not appear for normal users
- UI actions align with backend permissions

---

## Phase 8 Review

### What Phase 8 Covers

- source import
- URL/title/timestamp normalization
- RSS polling
- ingestion item persistence
- dedupe
- publication/review gating
- ingestion moderation UI
- source failure visibility

### Focused Automated Tests

```bash
uv run --package rifthub-api pytest \
  apps/api/tests/test_ingestion_foundation.py \
  apps/api/tests/test_ingestion_persistence.py \
  apps/api/tests/test_ingestion_publication.py \
  apps/api/tests/test_ingestion_polling.py \
  apps/api/tests/test_moderation.py \
  apps/api/tests/test_user_roles.py -q
```

```bash
uv run --package rifthub-worker pytest \
  apps/worker/tests/test_poll_rss_sources_job.py \
  apps/worker/tests/test_scheduler.py -q
```

### Manual Product Checks

Important note:

- the committed approved source file is still dummy development data
- that means a true end-to-end ingestion content review is limited unless you temporarily load a real working RSS source in local development

Manual checks that still make sense now:

1. run:

```bash
npm run db:seed:sources
```

2. log in as:

- admin
- moderator

3. open `/moderation`

Verify:

- ingestion review panel renders
- source health panel renders
- moderators can view ingestion queue but cannot approve/reject
- admins can approve/reject
- ingestion actions are admin-only and still auditable

If you want a real end-to-end ingestion review:

- replace one local dev source with a real reachable RSS feed in local development only
- reseed sources
- run the worker
- then inspect staged/published items through `/moderation` and the main feed

### Code Review Order

#### Slice 1: source import

Read:

- [ingestion_sources.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/ingestion_sources.py)
- [seed-approved-sources.py](/Users/telasi/Developer/RiftHub/scripts/seed-data/seed-approved-sources.py)
- [INGESTION_SOURCE_FORMAT.md](/Users/telasi/Developer/RiftHub/docs/agent-review/INGESTION_SOURCE_FORMAT.md)

Verify:

- importer only uses fields it documents
- unsupported source types are not silently executed

#### Slice 2: normalization

Read:

- [ingestion_normalization.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/ingestion_normalization.py)
- [domains.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/domains.py)

Verify:

- normalization is deterministic
- common tracking params are removed
- malformed input fails safely

#### Slice 3: polling

Read:

- [ingestion_polling.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/ingestion_polling.py)
- [poll_rss_sources.py](/Users/telasi/Developer/RiftHub/apps/worker/src/rifthub_worker/jobs/poll_rss_sources.py)

Verify:

- only active RSS sources are polled
- ETag and Last-Modified are persisted
- one broken source does not stop the batch

#### Slice 4: persistence and dedupe

Read:

- [ingestion_persistence.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/ingestion_persistence.py)
- [models/ingestion.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/models/ingestion.py)
- [20260324_03_ingestion_item_url_fallback_uniqueness.py](/Users/telasi/Developer/RiftHub/apps/api/alembic/versions/20260324_03_ingestion_item_url_fallback_uniqueness.py)

Verify:

- duplicate-safe insert/update logic is explicit
- source-local fallback uniqueness exists for items without `external_id`
- dedupe marks ingestion items instead of creating duplicate posts

#### Slice 5: publication

Read:

- [ingestion_publication.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/ingestion_publication.py)

Verify:

- auto-publish path still creates normal posts
- system-user attribution is deliberate
- review-first sources stop at `awaiting_review`

#### Slice 6: review and source visibility

Read:

- [routes/moderation.py](/Users/telasi/Developer/RiftHub/apps/api/src/rifthub_api/routes/moderation.py)
- [ingestion-review-panel.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/moderation/ingestion-review-panel.tsx)
- [OPERATIONS_ROLES.md](/Users/telasi/Developer/RiftHub/docs/agent-review/OPERATIONS_ROLES.md)

Verify:

- moderators can view but not approve/reject
- admins can approve/reject
- ingestion review stays inside the moderation surface
- source health is visible without reading worker logs directly

---

## Final Closeout Before Phase 9

If all four phase reviews are clean, do one final confidence pass:

```bash
uv run --package rifthub-api pytest apps/api/tests -q
```

```bash
uv run --package rifthub-worker pytest apps/worker/tests -q
```

```bash
npm run build --workspace @rifthub/web
```

If you want one combined human review checklist for launch-readiness after this, the next document should be a dedicated Phase 9 guide rather than extending this one further.
