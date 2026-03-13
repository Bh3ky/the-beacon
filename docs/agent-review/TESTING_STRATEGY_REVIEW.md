# TESTING_STRATEGY Review

## Session

- Date: 2026-03-13
- Stage: Phase 0 - Docs review
- Source reviewed this session: `docs/TESTING_STRATEGY.md`

## Syntax cleanup completed

I made safe consistency fixes directly in `docs/TESTING_STRATEGY.md`:

- added explicit auth/session and CSRF test coverage
- aligned API endpoint integration examples with the current API route shapes
- added moderation audit-record expectations to moderation workflow tests
- updated ingestion tests to reflect the review-first launch posture
- corrected the user registration E2E flow so it validates authenticated access instead of a vague dashboard assumption
- added explicit ranking/feed coverage for jobs being excluded from `top` and for the raw-vote-only v1 model
- expanded the launch checklist to include auth/session and CSRF coverage

These were testing-scope alignment fixes, not a testing philosophy rewrite.

## Findings

### 1. Auth and browser-security testing had been underspecified

Before this review, the testing doc did not explicitly cover the chosen v1 auth model:

- HTTP-only cookie sessions
- CSRF validation
- origin checks on mutating requests

Impact:

- high
- these are easy places to ship subtle but serious regressions if they are not part of the planned test suite

Action taken:

- added explicit auth/session test coverage
- added launch-checklist coverage for auth/session and CSRF testing

### 2. Ingestion tests still reflected the older auto-publish posture

The ingestion trust section previously expected:

- trusted source auto-publishes
- low-trust source enters moderation queue

But the resolved launch rule is:

- all sources are review-first at MVP launch
- no sources auto-publish at launch

Impact:

- high
- outdated test expectations would push implementation in the wrong direction

Action taken:

- updated the ingestion trust and E2E ingestion flow sections to match the review-first launch posture

### 3. Ranking and feed tests needed to encode the jobs/feed split explicitly

The ranking and feed sections were broadly correct, but they did not explicitly test two now-fixed product rules:

- jobs stay out of the main `top` feed
- v1 ranking uses raw vote counts only

Impact:

- medium
- if these are not captured in tests, later regressions can quietly reintroduce the wrong feed behavior

Action taken:

- added those expectations to ranking and feed generation coverage

### 4. Moderation testing needed to mention auditability directly

The project has repeatedly fixed auditability as a core moderation guardrail.

The moderation workflow tests previously focused on content removal outcomes, but not on whether the action was auditable.

Impact:

- medium
- moderation without audit verification is incomplete for this project

Action taken:

- added moderation action record expectations to the workflow coverage

### 5. The overall testing direction is now well aligned

The document is otherwise strong:

- it prioritizes the right critical systems
- it separates unit, integration, and end-to-end testing sensibly
- it gives ingestion, moderation, and ranking the attention they deserve
- it keeps UI testing secondary to core behavioral correctness

This file is now much more useful as an implementation guide.

## Clarification questions

No new product-blocking questions were introduced by this file review.

## Recommendation for next session

Next source file in the fixed order:

- `docs/Qs.md`

Reason:

- the testing strategy is now aligned with the core product and security decisions
- the final remaining doc in the review order should now be checked for any unresolved questions that need to be promoted into explicit decisions or tracked open items
