# MEMORY.md

## Current Working Rules

- Current project stage: `Phase 0 - Docs review completed`
- Next planned stage: `Phase 1 - Project foundation scaffold`
- Review only one source document per session
- Do not bulk-review docs in a single session
- Source-doc review order is fixed unless you explicitly change it
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

## Resolved Product Decisions

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
