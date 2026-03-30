# Phase 6 Worker Plan

Date: `2026-03-24`
Status: `review-ready`

## Goal

Introduce the first real worker system for ranking refresh, feed snapshot refresh, reconciliation, and cleanup without moving business logic ownership out of the shared backend package.

Phase 6 should add runtime orchestration and periodic execution, not invent a second copy of domain logic.

## Source Inputs

- [ROADMAP.md](/Users/telasi/Developer/RiftHub/docs/ROADMAP.md)
- [SYSTEM_ARCHITECTURE.md](/Users/telasi/Developer/RiftHub/docs/SYSTEM_ARCHITECTURE.md)
- [ARCHITECTURE.md](/Users/telasi/Developer/RiftHub/docs/ARCHITECTURE.md)
- [REPO_STRUCTURE.md](/Users/telasi/Developer/RiftHub/docs/REPO_STRUCTURE.md)
- [RANKING_SYSTEM.md](/Users/telasi/Developer/RiftHub/docs/RANKING_SYSTEM.md)
- [DEVELOPMENT_TEST_CHECKPOINTS.md](/Users/telasi/Developer/RiftHub/docs/agent-review/DEVELOPMENT_TEST_CHECKPOINTS.md)
- [MEMORY.md](/Users/telasi/Developer/RiftHub/docs/agent-review/MEMORY.md)
- [PHASE5_RANKING_PLAN.md](/Users/telasi/Developer/RiftHub/docs/agent-review/PHASE5_RANKING_PLAN.md)

## Current Code Reality

The repo now has a real first-pass worker runtime:

- [pyproject.toml](/Users/telasi/Developer/RiftHub/apps/worker/pyproject.toml)
- [main.py](/Users/telasi/Developer/RiftHub/apps/worker/src/rifthub_worker/main.py)

Current Phase 6 progress:

- worker runtime now has a simple async scheduler scaffold
- initial Phase 6 job registry now exists:
  - `refresh_post_scores`
  - `refresh_feed_snapshots`
  - `reconcile_vote_counts`
  - `expire_job_posts`
- placeholder job modules are wired with structured logging
- focused worker scheduler tests now exist
- `refresh_post_scores` now uses a real shared backend refresh path
- `expire_job_posts` now uses a real shared backend expiry-policy enforcement path
- `refresh_feed_snapshots` now writes Redis-backed expiring feed snapshots
- `reconcile_vote_counts` now repairs post/comment vote counters, scores, and rank fields from canonical vote tables

Important Phase 5 handoff state:

- ranking formulas and synchronous write-path updates now exist in the backend package
- feeds already read from persisted `rank_score`
- jobs feed logic already exists in the read layer
- Redis is already present in the stack and now used for API auth rate limiting

Phase 6 should therefore focus on:

- worker runtime orchestration
- scheduled execution
- Redis-backed snapshot and lock primitives where appropriate
- reconciliation and refresh jobs that reuse backend logic

## Locked Phase 6 Constraints

- worker remains a separate runtime from the API service
- worker does not expose a public HTTP surface
- shared domain logic stays in `packages/backend`
- Redis is an accelerator and coordination layer, not the source of truth
- Postgres remains canonical for scores, posts, votes, and moderation state
- Phase 6 workers refresh and reconcile state; they do not replace already-correct synchronous business logic from Phase 5

## Required Jobs

Phase 6 should implement these initial jobs:

- `refresh_post_scores`
- `refresh_feed_snapshots`
- `reconcile_vote_counts`
- `expire_job_posts`

## Recommended Structure

Use the existing worker app as the runtime shell and expand it roughly toward the repo-structure target:

```text
apps/worker/src/rifthub_worker/
  jobs/
    refresh_post_scores.py
    refresh_feed_snapshots.py
    reconcile_vote_counts.py
    expire_job_posts.py
  runners/
    scheduler.py
    locks.py
  main.py
```

If shared logic is needed, place it in `packages/backend/src/rifthub_backend/` and keep the worker app thin.

## Implementation Plan

### Slice 1: Worker runtime and scheduling

- replace the current no-op worker runner with a simple scheduler loop
- register the initial Phase 6 jobs in one place
- make job intervals explicit and easy to inspect
- log startup, job start, job success, and job failure

Deliverable:

- worker process starts and runs predictable scheduled jobs locally

Current status:

- implemented

### Slice 2: Ranking refresh job

- add a job that recomputes persisted `posts.rank_score` for the intended active window
- keep the Phase 5 ranking formula as the only source of scoring logic
- prefer calling shared backend helpers rather than rewriting ranking math inside the worker
- define the initial refresh window conservatively

Recommended initial focus:

- posts created in the last 72 hours
- posts with recent comments
- posts eligible for ranked feeds

Deliverable:

- periodic score refresh without formula drift

Current status:

- implemented for the initial recent-post window
- still needs future refinement around window tuning and later feed-snapshot integration

### Slice 3: Feed snapshot refresh

- define a Redis snapshot format for:
  - `top`
  - `new`
  - `ask`
  - `show`
  - `jobs`
- keep snapshots small and deterministic
- include timestamp metadata
- align TTLs with the ranking/system docs

Deliverable:

- worker-generated feed snapshots ready for read-path integration later in the API

Current status:

- implemented with Redis-backed expiring JSON snapshots for `top`, `new`, `ask`, `show`, and `jobs`
- current snapshot payload is intentionally minimal:
  - ordered post IDs
  - generated timestamp
  - TTL
  - pagination metadata

### Slice 4: Reconciliation and cleanup

- add vote/count reconciliation checks against canonical DB state
- add job expiry handling for job posts
- make these jobs idempotent
- ensure failures are logged clearly

Deliverable:

- basic maintenance jobs that can be rerun safely

Current status:

- implemented
- current `expire_job_posts` behavior enforces the bounded `30` day job-expiry policy on active job rows by backfilling missing expiry timestamps and clamping overly long expiry windows
- vote-count reconciliation now repairs post and comment counter drift from canonical vote tables

### Slice 5: Coordination and safety

- add worker lock primitives for jobs that must not overlap
- keep lock ownership simple and observable
- avoid introducing a heavy queue system at this stage
- define failure behavior and retry posture explicitly

Deliverable:

- duplicate execution control for scheduled jobs

## Validation

Phase 6 validation should include:

- worker boot tests
- scheduled job execution tests
- idempotency tests
- duplicate-execution control tests
- worker failure and retry tests
- cache refresh tests
- stale job cleanup tests
- observability/log emission checks

## Exit Criteria

Phase 6 is complete when all of the following are true:

- worker process boots and schedules jobs predictably
- ranking refresh jobs run without changing Phase 5 ranking semantics
- feed snapshot refresh runs and stores deterministic snapshot data
- reconciliation jobs are idempotent
- expired jobs are cleaned up consistently
- overlapping runs are controlled
- failures are observable enough that silent worker degradation is unlikely

## Implementation Status

Completed:

- Slice 1: scheduler scaffold and job registration
- Slice 2: real `refresh_post_scores`
- Slice 3: real `expire_job_posts` with the 30-day bounded expiry policy
- Slice 4: real `refresh_feed_snapshots` and `reconcile_vote_counts`
- Slice 5: Redis-backed duplicate-execution control for overlapping worker instances
  Locking approach: Redis lease keys with `SET ... NX EX` on acquire and owner-checked release

Current posture:

- worker jobs remain simple periodic tasks
- business logic stays in `packages/backend`
- Redis now handles both feed snapshots and worker coordination locks
- overlapping runs skip cleanly instead of double-executing the same scheduled job

## Recommended Next Step

Phase 6 is complete enough for manual review.

Next planned stage:

- Phase 7 moderation
