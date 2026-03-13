# INGESTION_PIPELINE Review

## Session

- Date: 2026-03-13
- Stage: Phase 0 - Docs review
- Source reviewed this session: `docs/INGESTION_PIPELINE.md`

## Syntax cleanup completed

I made safe consistency fixes directly in `docs/INGESTION_PIPELINE.md`:

- aligned source quality wording with the approved `active` / `paused` / `disabled` source model
- aligned moderation controls with pause/disable source operations
- renamed the older "ingestion queue" language to "ingestion lifecycle"
- updated the persisted ingestion status list to match the approved schema direction
- clarified that `auto_publish` skips manual review for trusted sources rather than bypassing all moderation concerns
- added `scraper` back to the documented `source_type` examples
- clarified the review-required source pipeline and summary wording

These were lifecycle and terminology fixes, not a pipeline redesign.

## Findings

### 1. Ingestion item lifecycle had drifted from the approved schema

Before this review, the file still used older states such as:

- `queued`
- `approved`

But the approved persisted lifecycle now is:

- `discovered`
- `normalized`
- `duplicate`
- `classified`
- `awaiting_review`
- `published`
- `rejected`
- `failed`

Impact:

- high
- inconsistent lifecycle names break worker logic, admin filters, moderation review expectations, and API/client assumptions

Action taken:

- updated the lifecycle section to use the approved persisted statuses only
- clarified the review-required flow using `awaiting_review`

### 2. Source-state wording needed to match the operational source model

The file still talked about "blocked sources" even though the approved operational source state is:

- `disabled`

Impact:

- medium
- source-control wording should match the actual DB/API/state vocabulary used elsewhere

Action taken:

- normalized the source-quality and moderation-control wording to `disabled`

### 3. `auto_publish` is still a real launch-policy decision

This file recommends:

- enabling auto-publish for high-trust publishers

That may be valid later, but the project has also explicitly prioritized early moderation so the system can be tuned during MVP development.

Impact:

- medium to high
- this affects moderation workload, launch safety, source onboarding, and how quickly low-quality external content can enter the feed

Recommendation:

- decide whether MVP launch should:
  - allow auto-publish for a very small trusted subset
  - or start review-first for all sources and enable auto-publish later

My recommendation:

- launch review-first for all sources
- only enable `auto_publish` after the initial approved source list is defined and moderation outcomes are observed

Reason:

- it is safer operationally
- it gives you better early moderation feedback
- it reduces the chance of low-quality ingestion becoming normalized before policy tuning is finished

### 4. The approved source list is still not actually defined

This document names several example publishers and suggests seeding 15–30 or 20–30 trusted sources, but it still does not define the real approved list.

Impact:

- medium
- ingestion implementation, tests, moderation workload, and launch readiness all depend on the actual source set

Recommendation:

- define the first approved source list explicitly rather than leaving it as illustrative examples

### 5. The rest of the ingestion direction is broadly aligned

The document is otherwise in good shape:

- dedupe and normalization are emphasized correctly
- published ingested posts enter the same ranking universe as user posts
- source metadata and moderation gates align better with the schema now
- worker-based orchestration still matches the system architecture and service-boundary docs

This file is much closer to implementation-ready after the lifecycle cleanup.

## Clarification answers received

Resolved on 2026-03-13:

1. At MVP launch, all ingestion sources should start review-first.
2. No sources should auto-publish at MVP launch.

Still open:

3. The actual first approved source list still needs to be defined explicitly.

## Recommendation for next session

Next source file in the fixed order:

- `docs/MVP_SCOPE.md`

Reason:

- ingestion is now closer to the approved schema and worker model
- the next useful check is whether the MVP scope still reflects the accumulated decisions about moderation, jobs visibility, auth, ranking, and ingestion launch posture
