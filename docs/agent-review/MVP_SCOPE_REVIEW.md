# MVP_SCOPE Review

## Session

- Date: 2026-03-13
- Stage: Phase 0 - Docs review
- Source reviewed this session: `docs/MVP_SCOPE.md`

## Syntax cleanup completed

I made safe consistency fixes directly in `docs/MVP_SCOPE.md`:

- added an explicit MVP jobs surface
- corrected submission typing so `show` is treated as a category rather than a post type
- aligned flag reasons with the enum-backed moderation vocabulary
- expanded the MVP category list to include `ask` and `show`
- removed the stale inline ranking formula and replaced it with high-level MVP ranking rules that defer to `RANKING_SYSTEM.md`
- aligned the ingestion description with the resolved review-first launch posture
- updated the launch strategy to seed approved review-first ingestion sources

These were scope-alignment fixes, not a product rewrite.

## Findings

### 1. Jobs visibility had not been made explicit enough in MVP scope

The project had already resolved that jobs are visible in the first MVP and live on a dedicated `/jobs` surface, with job posts excluded from the main `top` feed.

This document did not make that surface explicit enough before this review.

Impact:

- medium
- MVP scope should make visible user-facing surfaces unambiguous so implementation order and UI priorities stay clear

Action taken:

- added a dedicated jobs feed surface
- marked `jobs feed` as a required MVP feature

### 2. `show` had drifted toward a post-type interpretation

The submission section previously listed:

- `show` as a supported type

But the resolved product decision is:

- `show` is a category, not a post type

Impact:

- high
- this affects schema, API validation, submission UI, and downstream ranking/category logic

Action taken:

- corrected the submission section so only real post types are listed
- added a note clarifying how `show` should be represented

### 3. MVP scope was duplicating outdated ranking specifics

This document previously included:

- its own formula
- a different gravity suggestion

That conflicts with the rule that the ranking document should remain the source of truth.

Impact:

- high
- duplicated ranking math in multiple docs creates drift quickly and can mislead implementation

Action taken:

- removed the inline formula details
- replaced them with the already-resolved MVP ranking posture:
  - raw vote counts only
  - no weighted voting in v1
  - separate jobs feed logic

### 4. Ingestion scope had not yet reflected the review-first launch rule

The MVP doc still implied trusted-source auto-publish patterns and generic ingestion seeding language.

Impact:

- medium to high
- MVP scope should reflect the actual launch safety posture, especially because moderation is intentionally being tuned early

Action taken:

- updated the ingestion section to say all sources are review-first at launch
- clarified that no sources auto-publish at MVP launch
- updated the launch strategy wording accordingly

### 5. The approved source list is still the main remaining MVP-scope gap

This file still uses illustrative examples for ingestion sources rather than a real approved list.

Impact:

- medium
- MVP scope should eventually name the actual initial source set or explicitly link to where that list lives

Recommendation:

- define the approved source list before implementation planning moves into ingestion execution

## Clarification questions

No new product-blocking questions were introduced by this file review.

The existing open ingestion question remains:

- the actual first approved source list still needs to be defined explicitly

## Recommendation for next session

Next source file in the fixed order:

- `docs/SECURITY.md`

Reason:

- MVP scope is now aligned with the major decisions already made across ranking, moderation, auth, and ingestion
- the next valuable check is whether the security doc fully reflects the resolved cookie-session, CSRF, moderation, and ingestion safety decisions
