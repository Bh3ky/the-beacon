# SECURITY Review

## Session

- Date: 2026-03-13
- Stage: Phase 0 - Docs review
- Source reviewed this session: `docs/SECURITY.md`

## Syntax cleanup completed

I made safe consistency fixes directly in `docs/SECURITY.md`:

- removed the old JWT-or-cookie ambiguity from the auth section
- aligned the security doc with the resolved HTTP-only cookie-session model
- added explicit CSRF and `Origin` validation requirements for mutating requests
- tightened the CORS section to reflect credentialed cookie-based requests
- replaced stale JWT secret references with session and CSRF secret wording
- expanded the launch checklist to include CSRF and cross-origin cookie verification

These were security-contract alignment fixes, not a security redesign.

## Findings

### 1. Authentication security wording had drifted from the resolved v1 auth model

Before this review, the file still described sessions as if v1 could use:

- JWT tokens
- or secure HTTP-only cookies

But the project has already fixed the v1 auth direction as:

- server-side HTTP-only cookie sessions
- CSRF protection on mutating routes
- credentialed cross-origin requests only for explicit allowlisted origins

Impact:

- high
- security docs must be precise here because auth, browser behavior, and deployment boundaries are easy to implement incorrectly

Action taken:

- updated the file so the auth section reflects the resolved session-cookie direction only

### 2. CSRF and credentialed CORS needed to be explicit, not implied

The old version mentioned secure cookies, but it did not explicitly capture:

- CSRF validation
- `Origin` validation
- the no-wildcard rule for credentialed CORS
- the requirement to keep the CSRF token out of `localStorage`

Impact:

- high
- these are core browser-security requirements for the chosen auth model

Action taken:

- added an explicit CSRF and origin-protection section
- tightened the CORS section to match the chosen cookie-session flow

### 3. Secret classification needed to match the actual auth implementation

The secrets section still referred to:

- JWT keys

That no longer matches the chosen auth direction.

Impact:

- medium
- secret inventories should reflect real implementation requirements so env management and rotation planning are accurate

Action taken:

- replaced JWT-secret wording with session-signing/session-store secrets and CSRF secrets

### 4. The overall security direction is otherwise aligned

The document is otherwise in good shape:

- role checks remain server-side
- Redis is treated as a protected infrastructure component, not a public dependency
- ingestion sanitization is called out explicitly
- moderation and admin actions are treated as auditable
- the launch checklist covers the right general areas after the auth update

This file now aligns much better with the reviewed auth, moderation, ingestion, and system-architecture docs.

## Clarification questions

No new product-blocking questions were introduced by this file review.

## Recommendation for next session

Next source file in the fixed order:

- `docs/TESTING_STRATEGY.md`

Reason:

- the security contract is now aligned with the resolved auth and browser-boundary decisions
- the next useful review is whether the testing strategy actually covers these security, moderation, ingestion, and ranking constraints
