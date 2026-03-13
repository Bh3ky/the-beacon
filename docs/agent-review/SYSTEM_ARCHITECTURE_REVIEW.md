# SYSTEM_ARCHITECTURE Review

## Session

- Date: 2026-03-13
- Stage: Phase 0 - Docs review
- Source reviewed this session: `docs/SYSTEM_ARCHITECTURE.md`

## Syntax cleanup completed

I made small, safe consistency fixes directly in `docs/SYSTEM_ARCHITECTURE.md`:

- aligned the authenticated-user boundary with the resolved cookie-session and CSRF model
- aligned the post detail request flow with the slug-aware post route
- added explicit auth-boundary notes for `HttpOnly` session cookies, CSRF validation, origin validation, and credentialed CORS allowlists
- added cross-origin cookie verification to the production-readiness checklist
- tightened scheduler wording so worker triggers stay private and do not contradict the no-public-worker-surface rule

These were runtime-contract alignment fixes, not a topology redesign.

## Findings

### 1. Auth and browser security boundaries had been underspecified

Before this review, the runtime architecture still described session handling only loosely and did not encode the already-decided deployment constraints for:

- HTTP-only cookie sessions
- CSRF validation
- origin validation
- credentialed CORS with explicit allowlists

Impact:

- high
- this affects real production behavior across Vercel, Railway, cookies, and browser request handling

Action taken:

- updated the doc so the runtime boundary now reflects the resolved v1 auth model

### 2. The post-detail request flow lagged behind the canonical slug-aware route

The frontend structure already used:

- `/post/[id]/[slug]`

But the runtime flow still showed:

- `GET /posts/{id}`

Impact:

- medium
- this creates confusion when mapping frontend routing to backend fetch patterns

Action taken:

- updated the request flow to use `GET /posts/{id}/{slug}`

### 3. Worker scheduling guidance had a small boundary contradiction

This file correctly says workers should not expose public HTTP surfaces unless there is a strong operational need.

But the scheduling section also suggested:

- platform cron triggering a worker endpoint or command

Impact:

- low to medium
- without clarification, this could encourage a public worker trigger surface that weakens the boundary model

Action taken:

- tightened the wording to prefer worker commands or private internal endpoints behind platform controls

### 4. The overall runtime architecture is well aligned with the current project direction

The document is otherwise solid:

- modular monolith plus dedicated workers still fits the product
- Redis is correctly treated as an accelerator rather than the source of truth
- worker separation matches ranking, ingestion, and maintenance needs
- moderation and ingestion admin dependencies are represented clearly
- the scaling path remains conservative and appropriate for MVP

This file is implementation-oriented and broadly coherent with the reviewed docs so far.

## Clarification questions

No new product-blocking questions were introduced by this file review.

Implementation recommendation to keep in mind later:

- if deployment control allows it, prefer frontend and API origins that minimize cookie complexity while still preserving the explicit CORS and CSRF model

## Recommendation for next session

Next source file in the fixed order:

- `docs/SERVICE_BOUNDARIES.md`

Reason:

- the runtime topology is now aligned with the resolved auth and worker decisions
- the next logical check is whether the documented service boundaries still match the modular monolith direction and current ownership model
