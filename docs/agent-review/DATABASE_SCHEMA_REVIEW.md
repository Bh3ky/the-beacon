# DATABASE_SCHEMA Review

## Session

- Date: 2026-03-13
- Stage: Phase 0 - Docs review
- Source reviewed this session: `docs/DATABASE_SCHEMA.md`

## Syntax cleanup completed

I made safe documentation fixes directly in `docs/DATABASE_SCHEMA.md`:

- repaired malformed Markdown tables
- fixed malformed section headings
- normalized a few labels such as `Indexes` and `Columns`
- updated the optional session-table note to match the resolved HTTP-only cookie-session auth direction
- corrected a few list and formatting issues

These changes were structural and consistency-oriented, not a schema redesign.

## Findings

### 1. Ingestion status modeling conflicts with `INGESTION_PIPELINE.md`

`DATABASE_SCHEMA.md` currently defines:

- `new`
- `deduped`
- `queued`
- `published`
- `rejected`
- `failed`

But `INGESTION_PIPELINE.md` describes a richer state progression including:

- `discovered`
- `normalized`
- `duplicate`
- `queued`
- `classified`
- `awaiting_review`
- `approved`
- `published`
- `rejected`

Impact:

- high
- affects worker implementation, admin UI, API responses, and how much observability the ingestion pipeline has

Recommendation:

- choose one ingestion state model as authoritative
- if the richer pipeline states are real operational states, the enum here should reflect them
- if the richer pipeline is conceptual only, reduce that doc so it matches the persisted enum

### 2. Source status vocabulary may still be underspecified across docs

This schema uses:

- `active`
- `paused`
- `disabled`

But other docs also use language like:

- blocked sources
- trusted sources
- experimental sources

Impact:

- medium
- affects moderation controls, ingestion worker filtering, and admin UI behavior

Recommendation:

- decide whether "blocked" is a first-class source status, a moderation action, or just equivalent to `disabled`
- keep the source status model explicit across schema, ingestion, and moderation docs

### 3. `flags.reason_code` is free text rather than an enum

The schema uses:

- `reason_code` as `VARCHAR(64)`

This is flexible, but other parts of the system talk about a controlled set of reasons such as spam, abuse, misinformation, and off-topic.

Impact:

- medium
- affects admin filtering, analytics, moderation dashboards, and consistency of flag data

Recommendation:

- decide whether flag reasons should be:
  - a DB enum
  - a constrained lookup table
  - or application-controlled strings

### 4. Naming is still inconsistent with the rest of the docs set

This document previously used an older working name, while newer docs now use:

- `RiftHub`

Impact:

- low
- not a schema blocker, but it adds unnecessary ambiguity in the docs set

Recommendation:

- standardize the working name across docs once naming is finalized

Resolved later:

- standardized the working name to `RiftHub` across the docs set

### 5. The schema is generally aligned with resolved product direction

The good news:

- `show` appears only as a category, not a post type
- source modeling already uses `status`, `trust_score`, and `auto_publish`
- slug-aware route assumptions are compatible with `/post/{id}/{slug}`
- a `user_sessions` table now fits the chosen cookie-session auth model

This file is much closer to implementation-ready than the earlier umbrella docs.

## Clarification questions

These were resolved on 2026-03-13:

1. Persist a richer ingestion lifecycle in the database, but only for states with operational value.
2. Represent source blocking operationally as `status = disabled`.
3. Make `flags.reason_code` a real enum for MVP.
4. Treat `user_sessions` as a practical MVP schema table.

Applied direction:

- ingestion status is now modeled as a richer persisted lifecycle
- `disabled` is documented as the operationally blocked source state
- flag reasons are enum-backed
- `user_sessions` is documented as a practical MVP schema table

## Recommendation for next session

Next source file in the fixed order:

- `docs/API_SPEC.md`

Reason:

- the main unresolved schema questions around sessions, flags, and ingestion states will directly affect API contracts
- reviewing the API spec next will show whether those ambiguities are already resolved or still duplicated there
