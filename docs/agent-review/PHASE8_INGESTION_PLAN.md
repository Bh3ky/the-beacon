# Phase 8 Ingestion Plan

Date: `2026-03-24`
Status: `review-ready`

## Goal

Ship the first real ingestion pipeline for MVP so RiftHub can populate the site with approved external stories without bypassing ranking, moderation, or deduplication.

Phase 8 should introduce:

- approved source registry usage
- RSS polling
- normalization and dedupe
- ingestion item persistence
- auto-publish or moderation-gated publishing

It should not try to become a general web crawling platform.

## Source Inputs

- [ROADMAP.md](/Users/telasi/Developer/RiftHub/docs/ROADMAP.md)
- [INGESTION_PIPELINE.md](/Users/telasi/Developer/RiftHub/docs/INGESTION_PIPELINE.md)
- [SYSTEM_ARCHITECTURE.md](/Users/telasi/Developer/RiftHub/docs/SYSTEM_ARCHITECTURE.md)
- [ARCHITECTURE.md](/Users/telasi/Developer/RiftHub/docs/ARCHITECTURE.md)
- [REPO_STRUCTURE.md](/Users/telasi/Developer/RiftHub/docs/REPO_STRUCTURE.md)
- [MODERATION_POLICY.md](/Users/telasi/Developer/RiftHub/docs/MODERATION_POLICY.md)
- [MEMORY.md](/Users/telasi/Developer/RiftHub/docs/agent-review/MEMORY.md)
- [PHASE6_WORKER_PLAN.md](/Users/telasi/Developer/RiftHub/docs/agent-review/PHASE6_WORKER_PLAN.md)
- [PHASE7_MODERATION_PLAN.md](/Users/telasi/Developer/RiftHub/docs/agent-review/PHASE7_MODERATION_PLAN.md)

External references used to shape the plan:

- Python `urllib.parse` docs for URL parsing/normalization: https://docs.python.org/3/library/urllib.parse.html
- aiohttp client reference for request timeouts and HTTP client behavior: https://docs.aiohttp.org/en/stable/client_reference.html
- feedparser HTTP features and conditional requests:
  - https://feedparser.readthedocs.io/en/stable/http-etag.html
  - https://feedparser.readthedocs.io/en/releases/http.html
- feedparser bozo detection:
  - https://feedparser.readthedocs.io/en/stable/bozo.html
- SQLAlchemy asyncio transactions: https://docs.sqlalchemy.org/20/orm/extensions/asyncio.html
- SQLAlchemy PostgreSQL `ON CONFLICT` docs: https://docs.sqlalchemy.org/20/dialects/postgresql.html

## Current Code Reality

Already implemented:

- `sources` table exists in [source.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/models/source.py)
- `ingestion_items` table exists in [ingestion.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/models/ingestion.py)
- source/ingestion enums exist in [types.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/db/types.py)
- post schema already supports ingested provenance fields in [post.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/models/post.py)
- moderation enum surface already includes `approve_ingestion` and `reject_ingestion`
- worker runtime from Phase 6 already exists and can host scheduled ingestion jobs
- shared ingestion normalization helpers now exist in [ingestion_normalization.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/ingestion_normalization.py)
- approved source import logic now exists in [ingestion_sources.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/ingestion_sources.py)
- approved source seed script now exists in [seed-approved-sources.py](/Users/telasi/Developer/RiftHub/scripts/seed-data/seed-approved-sources.py)
- RSS polling and conditional fetch metadata now exist in [ingestion_polling.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/ingestion_polling.py)
- ingestion item persistence and URL-fallback dedupe now exist in [ingestion_persistence.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/ingestion_persistence.py)
- basic classification and publication flow now exist in [ingestion_publication.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/ingestion_publication.py)

Not implemented yet:

- no real approved source list loaded into the database

Important repo reality:

- [approved_sources.dev.json](/Users/telasi/Developer/RiftHub/scripts/seed-data/approved_sources.dev.json) is still dummy development data, not the real MVP source list

## Scope Decision

Phase 8 should implement the MVP ingestion subset only.

In scope:

- RSS-only ingestion for the first slice
- real approved source list import path
- source polling based on `poll_interval_minutes`
- feed parsing, normalization, dedupe, and staging
- auto-publish for trusted sources
- `awaiting_review` flow for review-required sources
- moderation actions to approve/reject staged ingestion items
- enough observability to see source failures

Explicitly out of scope for this phase:

- broad scraping support
- arbitrary API connectors
- ML classification
- full editorial CMS
- cross-source canonical HTML extraction beyond simple URL-based heuristics
- advanced retry orchestration or distributed queueing

## MVP Behavior

### Source types

For implementation, start with:

- `rss` only

Keep the model support for `api`, `manual`, and `scraper`, but do not build those runtimes in the first pass.

### Ingestion lifecycle

The persisted statuses already fit the spec and should remain the source of truth:

- `discovered`
- `normalized`
- `duplicate`
- `classified`
- `awaiting_review`
- `published`
- `rejected`
- `failed`

Recommended MVP flow:

```text
poll source
→ parse entries
→ insert/update ingestion item as discovered
→ normalize URL/title/date
→ dedupe against posts and prior ingestion items
→ classify
→ if source.auto_publish then publish
→ else move to awaiting_review
```

### Publishing rules

- auto-published items must still become normal posts and enter the ranking system like user submissions
- published ingested posts should preserve provenance via `is_ingested` and `ingested_from_source_id`
- duplicates should link to the existing post and should not create new posts
- review-required items should never become posts until an explicit approval action is taken

## Recommended Build Order

### Slice 1: source registry import

Add a real source import/seed path.

Deliverables:

- backend utility to load approved sources from JSON
- command entrypoint or script wrapper
- idempotent insert/update behavior for source rows

Current status:

- implemented for the current schema and dev source file format

Implementation notes:

- replace the dummy development-only source list with a real MVP-approved file before final rollout
- use explicit upsert behavior keyed by a stable source identity, likely name+url or a new slug field if needed
- prefer DB-level upsert semantics over check-then-insert races

### Slice 2: normalization helpers

Add shared ingestion normalization utilities in `packages/backend`.

Deliverables:

- URL normalization
- title cleanup
- timestamp normalization to UTC
- optional source/domain resolution helper

Current status:

- implemented

Implementation notes:

- use `urllib.parse` rather than ad hoc string slicing
- strip fragments and common tracking parameters
- keep the normalization rules deterministic and test-driven
- malformed URLs should fail into `failed` state rather than crash the worker

### Slice 3: RSS polling service

Add a shared backend polling service plus a worker job wrapper.

Deliverables:

- select due active RSS sources
- fetch feed content with bounded timeout
- parse entries with feedparser
- record per-source success/failure timestamps and error message fields

Current status:

- implemented, including conditional fetch metadata, per-source worker locking, and persisted polling error state

Implementation notes:

- support ETag and Last-Modified when sources provide them
- use bozo detection as warning/failure input, not silent acceptance
- do not let one broken source stop the rest of the polling batch
- add per-source locking in the worker using the existing Redis coordination pattern from Phase 6

### Slice 4: ingestion item persistence and dedupe

Store discovered items durably and dedupe them against existing content.

Deliverables:

- insert/update ingestion item rows
- source/external-id uniqueness handling
- URL dedupe against existing posts
- duplicate marking with `dedupe_match_post_id`

Current status:

- implemented, including a partial unique index for source-local URL fallback when feeds do not provide an external ID

Implementation notes:

- use DB uniqueness plus `ON CONFLICT` for race safety
- dedupe against `posts.url_normalized` first
- also guard against repeated ingestion of the same source item
- keep the ingest transaction narrow and explicit

### Slice 5: basic classification and publication

Add the first publish path.

Deliverables:

- source-default classification
- simple keyword-assisted category refinement
- publish-to-post flow for auto-publish sources
- `awaiting_review` staging for review-first sources

Current status:

- implemented for the MVP path:
  - source-default plus keyword-assisted category selection
  - auto-publish sources create normal ingested link posts
  - review-first sources stop at `awaiting_review`

Implementation notes:

- reuse the existing creation/domain logic where possible instead of creating posts by raw table insert
- initial post type can remain `link` for RSS items unless a clear jobs-specific source path is added later
- published posts should initialize rank fields the same way user-created posts do

### Slice 6: ingestion review and source visibility

Add the minimum operator surfaces needed to run ingestion safely.

Deliverables:

- moderation/admin API routes to list staged ingestion items
- approve/reject actions
- source failure visibility
- minimal web UI for ingestion review inside moderator/admin surfaces

Current status:

- implemented:
  - moderator queue read API for staged ingestion items
  - approve/reject moderation actions with per-item audit rows
  - source failure visibility API for operator review
  - `/moderation` web review panel for ingestion plus source-failure visibility

Implementation notes:

- keep this aligned with Phase 7 moderation patterns:
  - explicit role dependencies
  - audit rows for approve/reject actions
  - no public exposure of raw ingestion payloads

## Data and Schema Recommendations

The current schema is close, but Phase 8 may need a small follow-up migration.

Most likely missing fields:

- persisted source poll cache metadata such as `etag`
- persisted source poll cache metadata such as `last_modified`

Inference:

The spec strongly suggests conditional polling, but the current `sources` model only stores timing/error fields. To fully support efficient polling, we likely need one or both of:

- `last_etag`
- `last_modified_header`

If added, keep them on `sources`, not on each ingestion item.

## Validation Plan

Backend tests:

- source import is idempotent
- due-source selection respects status and poll interval
- polling failure records `last_error_at` and does not halt the batch
- ETag/Last-Modified short-circuit unchanged feeds correctly
- malformed feeds transition items or sources into visible failure states
- normalization strips tracking params deterministically
- dedupe marks duplicates instead of creating posts
- auto-publish sources create posts
- review-first sources stop at `awaiting_review`
- approve/reject actions update ingestion status and write audit rows

Worker tests:

- scheduler invokes ingestion polling job
- per-source lock prevents duplicate polling of the same source
- polling logs scanned/published/failed counts

Manual review focus:

- ingested stories clearly feel like normal ranked posts, not a separate feed
- provenance is still visible where appropriate
- duplicates do not leak through across repeated worker runs
- broken sources are visible to operators without reading raw logs only

## Exit Criteria

Phase 8 is complete enough when all of the following are true:

- approved RSS sources can be loaded into the database
- worker polling discovers and stores new ingestion items
- normalization and dedupe prevent obvious duplicates
- trusted sources can auto-publish to normal posts
- lower-trust sources land in `awaiting_review`
- moderators/admins can approve or reject staged items
- source failures are visible and do not silently stall the pipeline
- automated tests cover the core polling, dedupe, and publishing paths

Current assessment:

- the Phase 8 code path is review-ready
- the main non-code blocker is still product/ops: replace the dummy development approved-source seed file with the real MVP source list before rollout

## Recommendation

Treat Phase 8 as another thin-slice worker-backed system:

- start with RSS only
- keep normalization deterministic
- rely on DB constraints for race safety
- reuse Phase 6 worker coordination
- reuse Phase 7 moderation patterns for review actions

That should get RiftHub from “manual submissions only” to a credible MVP ingestion pipeline without prematurely building a general-purpose crawler platform.
