# SERVICE_BOUNDARIES Review

## Session

- Date: 2026-03-13
- Stage: Phase 0 - Docs review
- Source reviewed this session: `docs/SERVICE_BOUNDARIES.md`

## Syntax cleanup completed

I made small, safe consistency fixes directly in `docs/SERVICE_BOUNDARIES.md`:

- aligned the identity domain with the resolved cookie-session auth model
- replaced token-neutral wording with session-oriented wording
- named `user_sessions` explicitly in the ownership sections
- made the `domains` ownership matrix row less ambiguous by naming the ingestion-side implementation owner directly

These were boundary-clarity fixes, not a structural rewrite.

## Findings

### 1. Identity ownership had drifted from the resolved auth model

Before this review, the identity domain still used wording like:

- auth token/session creation
- sessions/auth tokens

That was broader than the current project decision, which is:

- server-side HTTP-only cookie sessions
- practical `user_sessions` support in the schema
- CSRF bootstrap and validation as part of the auth flow

Impact:

- medium
- token-neutral wording can create accidental implementation drift in a file that is supposed to define ownership boundaries

Action taken:

- updated the identity domain wording to center sessions and CSRF/session bootstrap responsibilities
- named `user_sessions` explicitly in the ownership matrix

### 2. `domains` ownership needed to be less ambiguous

This file correctly recognized that `domains` sit between ingestion and moderation concerns, but the ownership matrix previously described them only as shared.

Impact:

- medium
- shared ownership language often causes duplicated write paths and unclear mutation rules inside a monolith

Action taken:

- clarified the matrix so `domains` have an ingestion-side implementation owner with moderation-authorized mutation paths

This matches the practical direction already emerging across schema, ingestion, ranking, and moderation docs.

### 3. The rest of the boundary model is strong and aligned

The document is otherwise in good shape:

- posts, comments, votes, feeds, ranking, moderation, and ingestion are separated coherently
- published ingested posts correctly become post-domain objects after creation
- moderation-originated status changes are explicitly tied to auditability
- feeds depend on ranking semantics rather than inventing their own math
- the future extraction path still fits the modular monolith strategy

This is one of the cleaner planning docs in the set.

## Clarification questions

No new product-blocking questions were introduced by this file review.

## Recommendation for next session

Next source file in the fixed order:

- `docs/REPO_STRUCTURE.md`

Reason:

- the logical ownership model is now aligned with the current auth, moderation, ingestion, and ranking decisions
- the next practical check is whether the repository layout still supports those boundaries cleanly
