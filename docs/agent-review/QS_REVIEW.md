# Qs Review

## Session

- Date: 2026-03-13
- Stage: Phase 0 - Docs review
- Source reviewed this session: `docs/Qs.md`

## Syntax cleanup completed

I rewrote `docs/Qs.md` into a clearer planning document that now:

- separates resolved decisions from still-open questions
- fixes the malformed question/answer pairings from the older note-style version
- removes stale ambiguity where answers had already been decided elsewhere
- adds a usage rule so this file does not become a second source of truth again

I also synced newly confirmed decisions into `docs/agent-review/MEMORY.md`.

## Findings

### 1. The old file mixed resolved answers and open questions without structure

Before this review, `docs/Qs.md` was effectively a scratchpad:

- some items already had answers
- some were still open
- some answers were attached to the wrong questions
- some entries conflicted with later docs-review decisions

Impact:

- high
- this file could easily reintroduce confusion after other docs had already been normalized

Action taken:

- rewrote the file into `Resolved Decisions` and `Still-Open Questions`

### 2. Several important decisions were present here but not yet reflected in shared memory

This file contained useful resolved decisions such as:

- post edit window
- comment edit window
- repost window
- job expiry window
- source attribution for ingested content
- stricter anti-spam checks for early submissions

Impact:

- medium
- unresolved memory drift makes later implementation planning less reliable

Action taken:

- promoted those decisions into `docs/agent-review/MEMORY.md`

### 3. Some database-design questions remain open and should stay explicitly open

The final open set still includes implementation choices such as:

- `citext` for usernames
- email verification storage location
- whether hidden downvote support should exist internally from day one
- repost enforcement placement
- bookmark and `view_count` MVP posture
- source trust vs domain trust separation

These are valid open items and should remain visible until implementation planning resolves them.

### 4. The final docs-review phase is now mostly complete

At this point:

- the major product, auth, moderation, ranking, ingestion, and architecture contradictions have been normalized
- the remaining uncertainty is narrower and more implementation-oriented

This file now works as a clean question register instead of a confusing mixed notes page.

## Clarification questions

No new product-blocking questions were introduced by this file review.

The main remaining open items are already listed directly in:

- `docs/Qs.md`
- `docs/agent-review/MEMORY.md`

## Recommendation after this session

The fixed docs-review order is complete.

Next useful step:

- do a short Phase 0 wrap-up note summarizing:
  - what decisions are now locked
  - what questions remain open
  - what should happen before code starts
