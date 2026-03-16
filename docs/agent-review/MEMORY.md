# MEMORY.md

## Current Working Rules

- Current project stage: `Phase 1 - Project foundation scaffold completed`
- Next planned stage: `Phase 2 - Database and core models`
- Review only one source document per session
- Do not bulk-review docs in a single session
- Source-doc review order is fixed unless you explicitly change it
- Log ongoing implementation-review questions and answers under `curious_mind/` at the repo root so the running discussion history is preserved
- Working process:

```text
get question
→ analyze it
→ check docs
→ plan a response
→ ask follow-up questions
→ review with user
→ implement only after user is satisfied
```

## Product Summary

The product is a community-ranked discovery and discussion platform for African tech.

Core loop:

```text
discover → vote → discuss → submit
```

Primary value:

- aggregate signal across the African tech ecosystem
- rank stories through community participation
- avoid empty feeds through ingestion
- preserve quality through moderation

## Core Product Surfaces

- homepage feed
- `new` feed
- post detail page
- threaded comments
- post submission
- voting
- user profiles
- moderation tools
- ingestion admin tools

## Core Architecture

- frontend: Next.js on Vercel
- backend API: FastAPI on Railway
- database: PostgreSQL on Supabase
- cache: Redis on Upstash
- worker service: separate Railway worker for ingestion, ranking refresh, and maintenance

Architecture style:

- modular monolith
- separate worker processes
- managed infrastructure first

## Key Data Domains

- users
- posts
- comments
- post votes
- comment votes
- domains
- sources
- ingestion items
- flags
- moderation actions

## Key Behavioral Rules

- feed-first product
- public ranking should remain understandable
- upvote-first v1 behavior
- comments are retrieved flat and rendered as a tree client-side
- duplicate URLs should be normalized and deduped
- ingested content must not bypass ranking
- moderation actions should be auditable

## Ranking Guardrails

- use the ranking document as the source of truth
- do not duplicate ranking formulas in roadmap or implementation notes unless necessary
- lower-gravity hot ranking than high-volume global communities
- category and domain adjustments must stay subtle
- jobs use separate recency-first logic

## Security and Reliability Guardrails

- role checks must be server-side
- Redis is an accelerator, not the source of truth
- Postgres is the critical dependency
- worker failures must be observable
- secrets must be environment-managed
- required infrastructure config must fail fast; do not add silent fallback database URLs that can mask env-loading problems
- moderation and admin actions require auditability
- ingestion data must be sanitized before rendering

## Delivery Guardrails

- prioritize vertical slices
- build the core loop before extensions
- keep docs aligned with each other
- avoid introducing a second source of truth inside planning docs
- prefer high-level sequencing in roadmap docs and detailed behavior in dedicated specs
- use `docs/agent-review/DEVELOPMENT_TEST_CHECKPOINTS.md` as the recurring phase-by-phase test checklist during implementation
- use `docs/agent-review/PHASE0_WRAP_UP.md` as the transition summary between docs review and implementation planning
- use `docs/agent-review/PHASE1_FOUNDATION_PLAN.md` as the source of truth for the initial scaffold pass
- use `docs/agent-review/PHASE2_DATABASE_PLAN.md` as the source of truth for the next implementation slice

## Fixed Review Order

1. `ARCHITECTURE.md`
2. `DATABASE_SCHEMA.md`
3. `API_SPEC.md`
4. `RANKING_SYSTEM.md`
5. `MODERATION_POLICY.md`
6. `SYSTEM_ARCHITECTURE.md`
7. `SERVICE_BOUNDARIES.md`
8. `REPO_STRUCTURE.md`
9. `INGESTION_PIPELINE.md`
10. `MVP_SCOPE.md`
11. `SECURITY.md`
12. `TESTING_STRATEGY.md`
13. `Qs.md`

Review order status:

- completed in full during Phase 0

## Open Product Questions To Track

- approved initial ingestion source list contents

## Open Implementation Follow-Ups

- DB timestamp/default ownership cleanup before final codebase review and production readiness:
  - current state in `packages/backend/src/rifthub_backend/db/base.py` mixes ORM-side behavior and DB-side behavior for insert/update timestamp fields
  - `updated_at` is not purely database-driven today and can drift by write path
  - revisit this before the final codebase review and before any production deployment decision
  - preferred direction: make canonical audit timestamps database-owned, especially `created_at` and `updated_at`
  - do not leave the current mixed responsibility model as the long-term design
- User identity/index follow-up before final codebase review and production readiness:
  - `users.post_count` and `users.comment_count` now have non-negative DB constraints and should stay that way
  - email uniqueness semantics are still a design decision that must be made explicit across schema, validation, and auth flows
  - decide whether email handling is case-sensitive or canonicalized/case-insensitive, then implement that choice consistently
  - this decision must be made before signup/login/password-reset/email-verification flows are implemented
  - review whether `ix_users_role` is still worth keeping once real query patterns are clearer
- Domain/source trust semantics and indexing follow-up before final codebase review and production readiness:
  - `domains.submission_count` and `domains.published_post_count` now have non-negative DB constraints and should stay that way
  - `domains.trust_score > 0` is currently consistent with the schema docs and `sources.trust_score`, so do not change it casually in one model only
  - later decide whether trust score should remain strictly positive, become non-negative, or move to a bounded scale with explicit business meaning
  - review whether `ix_domains_is_blocked` should stay as a plain boolean index or become a more targeted partial index once real moderation/query patterns are known
- Source URL uniqueness and indexing follow-up before final codebase review and production readiness:
  - `sources.url` uniqueness policy is still unresolved
  - if each source row is meant to represent one canonical ingestion endpoint, duplicate sources should probably be disallowed
  - do not add a uniqueness constraint on raw `url` until source URL canonicalization rules are defined
  - once canonicalization rules are explicit, decide whether uniqueness belongs on raw `url`, normalized `url`, or a composite key such as `(source_type, url)`
  - review whether `ix_sources_auto_publish` should stay as a plain boolean index or become a targeted partial index if queries mostly care about `auto_publish = true`
- Vote schema expressiveness follow-up before final codebase review and production readiness:
  - `vote.py` is structurally clean as-is
  - later decide whether the unique one-vote-per-user-per-target rule should remain expressed as unique indexes or be rewritten as `UniqueConstraint` for clearer schema intent
- Moderation action semantics follow-up before final codebase review and production readiness:
  - `moderation.py` is acceptable as an append-only audit log
  - action-specific requirements for `reason` and `metadata_json` should be enforced in application/service logic for now
  - later decide whether moderation workflows are stable enough to justify DB-level checks for some action types
  - review whether moderation history queries need a composite index such as `(target_type, target_id, created_at)` once real query patterns are known
- Ingestion workflow semantics and indexing follow-up before final codebase review and production readiness:
  - `ingestion.py` ownership is strong, and the partial unique index on `(source_id, external_id)` where `external_id is not null` should stay
  - define allowed `ingestion_status` combinations in service logic, especially the rules tying together `ingestion_status`, `linked_post_id`, and `dedupe_match_post_id`
  - decide whether `url_normalized` is informational only or a real dedupe key with stronger uniqueness/dedupe semantics
  - revisit `discovered_at` default ownership during the broader timestamp/default cleanup pass
  - review queue-oriented partial indexes later for awaiting-review, failed-for-retry, and other status-specific ingestion worker paths once real query patterns exist
- Post dedupe and lifecycle follow-up before final codebase review and production readiness:
  - `posts.bookmark_count` and `posts.view_count` now have non-negative DB constraints and should stay that way
  - `posts.is_ingested` and `posts.ingested_from_source_id` now have a coherence constraint, but later revisit whether the boolean should exist at all or be inferred from source linkage
  - `posts.slug` is intentionally not globally unique under the current `id + slug` routing design; revisit only if route semantics change
  - decide explicit `posts.url_normalized` duplicate policy before production, especially for link-post dedupe and repost-window behavior
  - decide whether non-job posts must require `job_expires_at is null` and whether job posts need stricter expiry semantics
  - review active-post partial index opportunities later for rank, category-recency, type-recency, and active job expiry queries once real query patterns are known
- API packaging and tooling follow-up before final codebase review and production readiness:
  - keep `alembic` in `apps/api/pyproject.toml` as long as the migration environment and command surface continue to live under `apps/api`
  - if migration ownership moves into `packages/backend`, revisit whether Alembic should move with it
  - add `pytest-asyncio` later if direct async test coverage grows beyond the current sync/anyio-driven test style
  - consider `uvicorn[standard]` later only if dev/runtime ergonomics justify the extra dependency surface

## Resolved Product Decisions

- Phase 2 DB session lifecycle note:
  - problem:
    - `packages/backend/src/rifthub_backend/db/session.py` originally cached the async engine and session factory as module globals with first-call-wins behavior
    - if one startup or test path initialized the cache with one `Settings` value and a later path passed a different `Settings`, the later call silently reused the old engine or factory
    - this created hidden cross-test contamination and made in-process reconfiguration unsafe
  - solution:
    - cache reuse is now allowed only when the effective DB config matches the already-initialized cache
    - the effective cache key is `database_url` plus `sql_echo`
    - if a later call tries to use different DB settings, `get_engine()` and `get_session_factory()` now raise a `RuntimeError` that tells the caller to run `dispose_engine()` first
    - `dispose_engine()` now clears cached module state before awaiting disposal so a failing dispose does not leave stale cache state behind
    - targeted regression tests live in `apps/api/tests/test_db_session.py`
- moderation must be in place early enough to test and tune during MVP development
- jobs are visible in the first MVP
- v1 auth mode is HTTP-only cookie session
- auth requirements:
  - `HttpOnly`
  - `Secure`
  - `SameSite=Lax` or `SameSite=Strict` where possible
  - server-side session validation or signed session token
  - CSRF protection for state-changing requests
- the project needs a real approved source list, not placeholder source names
- `ARCHITECTURE.md` should be reduced to a high-level overview pointing to specialized docs
- newer specialized docs are authoritative when they conflict with `ARCHITECTURE.md`
- canonical frontend post route for v1 is `/post/[id]/[slug]`
- posts are editable for `15 minutes`
- comments are editable for `15 minutes`
- link reposts are allowed after `30 days`
- jobs expire automatically after `30 days`
- source model should standardize around `status`, `trust_score`, and `auto_publish`
- `show` remains a category, not a post type
- intended meaning of `show`: a feed/category for people showcasing what they built, such as open-source projects, launches, demos, and build-in-public style posts
- ingested content should carry source attribution
- new users' first `1-3` submissions may go through stricter anti-spam checks
- persist a richer ingestion lifecycle in the database where it has operator value
- source blocking is represented operationally as `status = disabled`
- `flags.reason_code` is enum-backed for MVP
- `user_sessions` is part of the practical MVP schema
- `domains` implementation ownership lives under ingestion services with moderation-authorized mutation paths
- MVP ingestion launch posture is review-first for all sources
- no sources auto-publish at MVP launch
- moderation appeals are manual/out-of-band at launch
- moderator warnings remain communication plus moderator notes only in v1
- v1 ranking uses raw vote counts only
- v1 does not enable lightweight weighted voting inside `rank_score`
- `post_type = job` posts are excluded from the main `top` feed in v1
- jobs remain visible through the dedicated `/jobs` surface and jobs feed only
- `GET /moderation/flags` is the canonical moderation flag review route namespace
- auth implementation direction for v1:
  - FastAPI backend uses server-side cookie sessions
  - session cookie is `HttpOnly`, `Secure`, and `SameSite=Lax` or `SameSite=Strict` where possible
  - use `validate_csrf` as a dependency on mutating routes
  - add origin-validation middleware for state-changing requests
  - enable credentialed CORS only for explicit allowed origins
- CSRF transport pattern for v1:
  - bootstrap the CSRF token on app mount
  - keep the CSRF token in frontend memory only
  - do not store CSRF tokens in `localStorage`
  - frontend auto-attaches the token on mutating requests via an Axios interceptor
  - frontend requests that need session auth must send credentials so the session cookie is included
- temporary development ingestion source seed lives at `backend/dev/approved_sources.dev.json` until the real approved source list is finalized
- planned repo rename: `the-beacon` -> `rifthub`
- planned shared Python package import name: `rifthub_backend`
