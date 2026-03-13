# Phase 2 Database Plan

## Purpose

This plan defines the Phase 2 implementation pass for `RiftHub`.

Phase 2 starts after the Phase 1 scaffold is complete.
Its job is to establish the persistent data layer so later API, ranking, moderation, and ingestion work can build on stable schema contracts.

This phase is intentionally about schema and persistence plumbing.
It is not the phase for building the full product loop yet.

## Inputs

This phase is grounded in:

- `docs/DATABASE_SCHEMA.md`
- `docs/ROADMAP.md`
- `docs/agent-review/DEVELOPMENT_TEST_CHECKPOINTS.md`
- `docs/agent-review/PHASE1_FOUNDATION_PLAN.md`

## Preconditions

Before Phase 2 starts:

- the monorepo scaffold from Phase 1 must already work
- `apps/api` and `apps/worker` must import `packages/backend`
- local Postgres must be available for development
- environment variables for database connectivity must be defined

## Goal

At the end of this phase, the repository should have:

- shared database configuration in `packages/backend`
- async SQLAlchemy engine and session plumbing
- declarative SQLAlchemy models for the core schema
- Alembic configured and generating the database schema
- an initial migration chain that can be applied and rolled back cleanly
- tests that prove constraints, enums, foreign keys, and uniqueness rules behave correctly

## Decisions Locked For This Phase

- database: PostgreSQL
- ORM layer: SQLAlchemy 2.x async
- migration tool: Alembic
- shared DB code lives in `packages/backend`
- API and worker stay thin and consume the shared backend package
- UUID primary keys remain the default for public-facing entities
- database enums should be created explicitly, not simulated loosely in app code

## Recommended Repository Additions

Add the shared database layer under `packages/backend`:

```text
packages/backend/src/rifthub_backend/
  db/
    __init__.py
    base.py
    session.py
    types.py
  models/
    __init__.py
    user.py
    domain.py
    post.py
    comment.py
    vote.py
    flag.py
    moderation.py
    source.py
    ingestion.py
    session.py
```

Add Alembic under `apps/api`:

```text
apps/api/
  alembic.ini
  alembic/
    env.py
    script.py.mako
    versions/
```

Reasoning:

- the API owns migration execution
- the shared backend package owns schema definitions and database primitives

## Implementation Scope

### 1. Shared database config

Extend shared settings to include:

- `database_url`
- optional sync migration URL if needed separately
- SQL echo toggle for local debugging

Expected result:

- API and Alembic can resolve DB settings from one shared source

### 2. SQLAlchemy base and session layer

Implement:

- declarative base
- naming conventions for constraints and indexes
- async engine factory
- async session factory
- dependency helper for API usage later

Expected result:

- one standard session setup is used across API code, tests, and migrations

### 3. Database enums

Create database-backed enums matching `docs/DATABASE_SCHEMA.md`:

- `user_role_enum`
- `user_status_enum`
- `post_type_enum`
- `post_status_enum`
- `comment_status_enum`
- `category_enum`
- `flag_target_type_enum`
- `flag_status_enum`
- `flag_reason_enum`
- `moderation_target_type_enum`
- `moderation_action_type_enum`
- `source_type_enum`
- `source_status_enum`
- `ingestion_status_enum`

Expected result:

- enum values are enforced in PostgreSQL, not just hinted in Python

### 4. Core models

Implement these tables in Phase 2:

- `users`
- `domains`
- `posts`
- `comments`
- `post_votes`
- `comment_votes`
- `flags`
- `moderation_actions`
- `sources`
- `ingestion_items`
- `user_sessions`

Optional supporting tables can be deferred unless they materially help migration structure:

- `post_score_history`
- `daily_stats`

Rationale:

- `user_sessions` is called out in the test checkpoints and auth direction
- `sources` and `ingestion_items` belong in the core schema, not as a later afterthought

### 5. Constraints and indexes

Implement the important integrity rules from `docs/DATABASE_SCHEMA.md`.

Must-have constraints:

- `users.username` unique
- `users.email` unique
- `domains.hostname` unique
- `post_votes (post_id, user_id)` unique
- `comment_votes (comment_id, user_id)` unique
- `vote_value in (-1, 1)` on vote tables
- `trust_score > 0` on `domains`
- `poll_interval_minutes > 0` and `trust_score > 0` on `sources`
- `depth >= 0` on `comments`
- non-negative count checks on `posts` and `comments`
- post-type conditional checks for `text`, `link`, and `job`
- partial uniqueness for ingestion `(source_id, external_id)` where `external_id is not null`

Must-have indexes:

- feed-oriented post indexes
- comment tree indexes
- moderation lookup indexes
- source and ingestion lifecycle indexes
- created-at/status indexes described in the schema doc

Special attention:

- `posts.url_normalized` dedupe behavior
- `flags.reason_code`
- `source_status_enum`
- `ingestion_status_enum`

### 6. Alembic setup and migrations

Create Alembic wiring that imports metadata from `packages/backend`.

Recommended migration shape:

1. enable required extensions if chosen
2. create enums
3. create foundational tables:
   - `users`
   - `domains`
   - `sources`
4. create content tables:
   - `posts`
   - `comments`
5. create interaction tables:
   - `post_votes`
   - `comment_votes`
   - `flags`
   - `moderation_actions`
   - `user_sessions`
6. create ingestion linkage:
   - `ingestion_items`
7. create indexes and partial indexes

Expected result:

- a new local database can be brought to current state with Alembic only

### 7. Test scaffolding

Add the first DB-focused tests.

Minimum test categories:

- migration up/down test
- enum creation test
- foreign key integrity test
- uniqueness tests for usernames and emails
- uniqueness tests for post votes and comment votes
- URL dedupe constraint test
- constraint tests for invalid `post_type` field combinations
- source polling/trust checks
- ingestion lifecycle enum coverage

## Suggested Execution Order

```text
extend shared config
→ add SQLAlchemy base/session plumbing
→ define enums
→ implement foundational models
→ implement content and interaction models
→ wire Alembic
→ create initial migrations
→ run migration up/down checks
→ add schema integrity tests
```

## Validation Checkpoints

Phase 2 is complete only if all of these hold:

1. Alembic can upgrade a fresh development database successfully.
2. Alembic can downgrade the migration set cleanly.
3. The created tables match the planned schema set.
4. The critical enums exist in the database with the correct values.
5. Foreign keys fail correctly on invalid references.
6. Unique constraints fail correctly for usernames, emails, and vote uniqueness.
7. Check constraints fail correctly for invalid vote values and invalid post-type field combinations.
8. URL dedupe-sensitive constraints behave as intended.
9. `user_sessions`, `flags.reason_code`, `source_status_enum`, and `ingestion_status_enum` are present and tested.

## Explicit Non-Goals

This phase should not drift into:

- auth route implementation
- session cookie issuance
- CSRF protection
- post submission endpoints
- comment endpoints
- vote endpoints
- ranking formulas
- worker polling logic
- moderation workflows
- frontend product pages

## Practical Deliverable

The main output of Phase 2 should be a repository state where the next phase can begin from a stable persistence layer:

```text
shared DB config
→ reusable async DB primitives
→ core SQLAlchemy models
→ Alembic migrations
→ schema integrity tests
```

## What Phase 3 Should Inherit

Once this phase is complete, Phase 3 should be able to build on:

- ready-to-use DB sessions
- reliable persistence models
- migration-backed local databases
- tested enum, FK, and uniqueness behavior

That enables the next slice:

```text
auth plumbing
→ post creation APIs
→ comment APIs
→ vote APIs
→ core feed read endpoints
```
