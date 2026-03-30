# Phase 5 Ranking Plan

Date: `2026-03-24`
Status: `ready for manual review`

## Goal

Use Phase 5 to finish, validate, and tighten the ranking system that already exists in partial form.

This is not a greenfield ranking build anymore. The repo already has:

- persisted `rank_score` on posts and comments
- a post hot-score formula in `packages/backend/src/rifthub_backend/voting.py`
- synchronous post rank recompute on post vote changes
- rank-ordered `top`, `ask`, and `show` feed queries in `packages/backend/src/rifthub_backend/reads.py`
- recency-first separation for the jobs feed

Phase 5 should therefore focus on:

- aligning the current implementation with the locked ranking docs
- closing ranking behavior gaps
- adding deterministic test coverage
- preparing a clean handoff into Phase 6 worker-based refresh

## Source Inputs

- [ROADMAP.md](/Users/telasi/Developer/RiftHub/docs/ROADMAP.md)
- [RANKING_SYSTEM.md](/Users/telasi/Developer/RiftHub/docs/RANKING_SYSTEM.md)
- [RANKING_SYSTEM_REVIEW.md](/Users/telasi/Developer/RiftHub/docs/agent-review/RANKING_SYSTEM_REVIEW.md)
- [DEVELOPMENT_TEST_CHECKPOINTS.md](/Users/telasi/Developer/RiftHub/docs/agent-review/DEVELOPMENT_TEST_CHECKPOINTS.md)
- [MEMORY.md](/Users/telasi/Developer/RiftHub/docs/agent-review/MEMORY.md)

## Locked Phase 5 Product Decisions

These are already resolved and should not be reopened during this phase:

- v1 ranking uses raw vote counts only
- v1 does not enable weighted voting inside `rank_score`
- `post_type = job` is excluded from the main `top` feed
- jobs remain visible only through the dedicated jobs surface and jobs API
- `top`, `ask`, and `show` use hot-score ordering with deterministic tie-breakers

## Current Code Reality

The current implementation is materially ahead of the original roadmap wording.

### Already implemented

- `posts.rank_score` exists and is indexed
- `comments.rank_score` now uses a documented comment hot-score formula
- `reads.py` orders `top`, `ask`, and `show` by ranked ordering with deterministic tie-breakers:
  - `rank_score DESC`
  - `submitted_at DESC`
  - `comment_count DESC`
  - `id DESC`
- `reads.py` keeps `new` and `jobs` recency-first
- `reads.py` excludes jobs from the main `top` feed
- `reads.py` excludes blocked domains from post feeds
- `voting.py` computes post hot score with:
  - gravity `1.4`
  - hours offset `3`
  - base vote score `score + 1`
- post rank now also applies:
  - bounded comment factor
  - category multiplier
  - domain trust clamp
- post vote changes update:
  - `upvote_count`
  - `downvote_count`
  - `score`
  - `rank_score`
- post creation initializes a nonzero starting `rank_score`
- comment creation initializes comment `rank_score` and refreshes parent post `rank_score`
- post and comment voting now reject self-votes
- post-page comment tree rendering now sorts siblings explicitly for `top`

### Still needs explicit Phase 5 review

- whether the current targeted test coverage is broad enough to count as true Phase 5 completion
- whether any non-public consumers rely on the old flat global comment ordering semantics
- whether we want a frontend test harness now or leave manual UI review as the final validation step for comment-thread ordering
- whether any moderation/category/domain-trust write paths should trigger rank refresh before Phase 6 worker jobs exist

## Implementation Plan

### Slice 1: Ranking audit and invariants

- audit all write paths that create or mutate posts and comments
- confirm which operations currently recalculate `rank_score`
- confirm that jobs never enter the main `top` feed query path
- confirm that category feeds inherit the same ranking semantics as `top`
- document any mismatch between the code and `RANKING_SYSTEM.md` before changing logic

Deliverable:

- a short implementation note or code comments only where the current flow is non-obvious

### Slice 2: Post ranking alignment

- ensure post creation writes a correct initial `rank_score`
- ensure post vote changes keep `score` and `rank_score` in sync
- ensure comment-side activity updates any intended post freshness fields consistently if the doc requires it
- make tie-breaker behavior explicit and stable across queries and cursors

Deliverable:

- one authoritative post-ranking implementation path

### Slice 3: Comment ranking decision and implementation

- verify the intended v1 behavior for post comment trees:
  - thread-first rendering
  - score-aware sibling ordering
- decide whether current `Comment.rank_score = float(score)` is sufficient for v1
- if it is sufficient, document and test that explicitly
- if it is not sufficient, implement the smallest ranking change that matches the doc without inventing a new ranking system

Deliverable:

- comment ranking behavior that is clearly intentional, documented, and covered by tests

### Slice 4: Test coverage and validation

Add or tighten:

- post ranking unit tests
- feed ordering integration tests
- deterministic tie-breaker tests
- `ask` and `show` ranking tests
- jobs-feed separation tests
- rank refresh trigger tests for vote-driven updates
- inactive/removed-content exclusion tests on ranked feeds

Current progress:

- ranking math helper coverage added
- creation-time rank initialization coverage added
- top-feed ranked query coverage added
- ask-feed ranked query coverage added
- jobs-feed recency/expiry coverage added
- comment top-sort query coverage added
- self-vote coverage added
- full API test suite passed via `uv run --package rifthub-api pytest apps/api/tests -q`
- full production web build passed via `npm run build --workspace @rifthub/web`

Manual review targets:

- a new post with one upvote should not dead-start at zero visibility
- a newer strong post can outrank an older weak post
- jobs remain visible in `/jobs` but absent from `/`
- equal `rank_score` ordering stays deterministic across pagination

## Out Of Scope For Phase 5

- weighted voting
- reputation-driven ranking
- cache snapshot refresh
- scheduled score refresh workers
- large anti-abuse heuristics beyond the existing moderation/rate-limit controls

Those belong to later phases unless a ranking bug forces a targeted exception.

## Hand-off To Phase 6

Phase 5 should leave the ranking layer in a state where Phase 6 can safely add worker-driven refresh without changing product semantics.

That means:

- the v1 formula is locked
- synchronous write-path rank updates are correct
- test coverage makes ranking regressions obvious
- any future worker jobs are refresh and reconciliation mechanisms, not a replacement for unclear business logic

## Exit Criteria

Phase 5 is complete when all of the following are true:

- feed ordering matches `RANKING_SYSTEM.md`
- raw vote counts remain the only v1 ranking input
- jobs are excluded from the main `top` feed
- jobs feed remains recency-first
- ranked queries use deterministic tie-breakers
- hidden/removed/inactive content is excluded from ranked surfaces
- ranking behavior is covered well enough that we can trust further work in Phase 6

## Current Assessment

Phase 5 is now code-complete enough to hand over for manual review.

What is complete:

- ranking formulas are aligned with the current docs
- write-path score updates are coherent for post votes, comment votes, post creation, and comment creation
- ranked feed query behavior is deterministic and covered
- comment `top` display behavior is now explicitly score-aware at the sibling level
- self-vote protection is enforced
- the full backend suite passes
- the production frontend build passes

What remains before formally closing the phase:

- your manual code review
- your manual product review of ranked feed and comment behavior in the UI

If those reviews are clean, Phase 6 can proceed without reopening the core Phase 5 implementation.
