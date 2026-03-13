# Phase 0 Wrap-Up

## Status

Phase 0 docs review is complete.

The fixed review sequence was completed in this order:

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

## What Phase 0 Achieved

- normalized the documentation set into a mostly consistent source of truth
- removed major cross-doc contradictions across auth, routing, schema, moderation, ranking, and ingestion
- established a practical implementation workflow: analyze, check docs, plan, ask follow-up questions, review, then implement
- created persistent project memory and review artifacts in `docs/agent-review/`
- added a recurring implementation test checklist in `DEVELOPMENT_TEST_CHECKPOINTS.md`

## Locked Decisions

- v1 auth uses server-side HTTP-only cookie sessions
- CSRF protection is required on all mutating routes
- CSRF token is bootstrapped on app mount and stored in frontend memory only
- origin validation middleware is required for state-changing requests
- credentialed CORS is restricted to explicit origins
- canonical post route is `/post/[id]/[slug]`
- `show` is a category, not a post type
- jobs are included in MVP but live on the dedicated `/jobs` surface
- v1 ranking uses raw vote counts only
- jobs are excluded from the main `top` feed
- moderation is in scope early so it can be exercised during MVP development
- ingestion launches as review-first for all sources
- no sources auto-publish at MVP launch
- source blocking is represented as `status = disabled`
- `flags.reason_code` is enum-backed for MVP
- `user_sessions` is part of the MVP schema
- moderation appeals are manual/out-of-band at launch
- moderator warnings remain communication plus notes only in v1

## Remaining Open Items

- define the initial approved ingestion source list

## Before Writing Production Code

- confirm the approved initial ingestion source list
- do a short implementation-planning pass for the first vertical slice
- keep `MEMORY.md` and `DEVELOPMENT_TEST_CHECKPOINTS.md` current as implementation decisions are made
- treat the specialized docs as authoritative over older umbrella summaries

## Recommended Next Step

Move from docs review into implementation planning for the first vertical slice:

```text
auth/session foundation
→ CSRF and origin enforcement
→ core schema and migrations
→ basic feed read path
→ post submission
→ moderation hooks
```
