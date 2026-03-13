# REPO_STRUCTURE Review

## Session

- Date: 2026-03-13
- Stage: Phase 0 - Docs review
- Source reviewed this session: `docs/REPO_STRUCTURE.md`

## Syntax cleanup completed

I made small, safe consistency fixes directly in `docs/REPO_STRUCTURE.md`:

- added explicit frontend/backend auth helper locations for CSRF-aware cookie-session auth
- aligned the `docs/` tree recommendation with the repo’s current flat-docs plus `agent-review/` structure
- updated the example full tree to match that current docs layout
- clarified that the build-order section is a repo bootstrap order, not a competing roadmap

These were structure-alignment fixes, not a repository redesign.

## Findings

### 1. Auth-related foldering needed to reflect the resolved session/CSRF model

Before this review, the repo structure already had auth folders, but it did not explicitly reflect the CSRF/session helper split we already decided on for v1.

Impact:

- medium
- repo structure docs should make the intended auth implementation shape obvious before code starts

Action taken:

- added `apps/web/lib/auth/csrf.ts`
- added `apps/api/app/api/deps/csrf.py`

This keeps the repo guidance aligned with the cookie-session, CSRF-validation, and frontend bootstrap model already captured in planning notes.

### 2. The recommended `docs/` layout no longer matched the actual project workflow

This file previously suggested moving docs into:

- `architecture/`
- `product/`
- `operations/`

But the current project is intentionally operating with:

- flat top-level docs during the review phase
- a dedicated `docs/agent-review/` folder for memory, review notes, and question tracking

Impact:

- medium
- recommending a different docs layout right now would create unnecessary churn while the docs are still being normalized

Action taken:

- updated the docs section and example tree to match the current repo reality
- documented `agent-review/` explicitly

### 3. The build-order section needed to avoid competing with the roadmap

The file included its own phase-like build order, which is useful for repo bootstrapping but can be mistaken for the authoritative implementation roadmap.

Impact:

- low to medium
- phase naming drift across docs creates confusion about what sequence actually governs implementation

Action taken:

- clarified that this section is a repo bootstrap order, not the source-of-truth product roadmap

### 4. The overall repository direction is well aligned with the current architecture

The document is otherwise strong:

- the monorepo layout fits the actual frontend/API/worker split
- API service structure matches the internal service-boundary doc
- worker orchestration stays separate from shared domain logic
- test placement is sensible by level and domain
- the repo discipline rules support the modular monolith direction well

This file is materially ready to guide actual scaffolding work.

## Clarification questions

No new product-blocking questions were introduced by this file review.

## Recommendation for next session

Next source file in the fixed order:

- `docs/INGESTION_PIPELINE.md`

Reason:

- the repo layout now supports the agreed app and domain boundaries
- the next high-value review is the ingestion pipeline, because it intersects worker behavior, source ownership, moderation gating, and ranking entry rules
