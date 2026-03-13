# RANKING_SYSTEM Review

## Session

- Date: 2026-03-13
- Stage: Phase 0 - Docs review
- Source reviewed this session: `docs/RANKING_SYSTEM.md`

## Syntax cleanup completed

I made small, safe consistency fixes directly in `docs/RANKING_SYSTEM.md`:

- clarified `jobs` feed eligibility so it matches the schema and API examples
- normalized the summary wording from "weighted vote signal" to "vote signal" so it does not overstate a decision that is still optional for v1

These were clarity fixes, not a redesign of the ranking model.

## Findings

### 1. Weighted voting is still not fully locked for v1

The file currently presents three slightly different positions:

- section `8.2` recommends lightweight weighted voting conceptually
- section `8.3` says a simpler MVP can use raw counts only
- section `8.4` says weighting can optionally exist only inside `rank_score`

Impact:

- high
- this affects how post votes and comment votes are interpreted, how `rank_score` is computed, and how much anti-abuse behavior is baked into the first launch

Recommendation:

- decide one explicit v1 default:
  - raw vote counts only
  - or lightweight weighting inside `rank_score` only
- keep raw displayed vote totals regardless

My recommendation:

- launch with raw vote counts only in v1
- keep the formula and config ready for lightweight weighted voting later if abuse or low-quality manipulation becomes real

Reason:

- it is easier to explain
- it matches the current "upvote-first" MVP posture
- moderation and anti-abuse controls are already being prioritized early

### 2. Top-feed treatment of job posts is still ambiguous

The doc now clearly defines the dedicated jobs feed, but the `top` feed section still says:

- if `post_type = job`, it is either excluded entirely or included only under special policy

Impact:

- medium to high
- affects homepage composition, cache snapshots, eligibility queries, and whether jobs can crowd out story discovery

Recommendation:

- decide the v1 policy explicitly

My recommendation:

- exclude `post_type = job` from the main `top` feed in v1
- keep jobs visible through `/jobs` and `GET /feeds/jobs`

Reason:

- the product already defines separate jobs logic
- users read jobs differently from ranked stories and discussions
- this avoids cluttering the main discovery surfaces

### 3. The ranking model is otherwise well aligned with the current docs set

The document is in good shape overall:

- `show` is treated as a category, not a post type
- jobs use separate recency-first logic
- domain trust stays subtle
- upvotes are public while downvotes remain disabled in the initial UI
- ingested content enters the same ranking pool once published
- persisted `rank_score` plus cached feed snapshots matches the system architecture direction

This file is much closer to implementation-ready than the older umbrella docs.

## Clarification answers received

Resolved on 2026-03-13:

1. v1 ranking should use raw vote counts only.
2. v1 should not enable lightweight weighted voting inside `rank_score`.
3. `post_type = job` should be excluded from the main `top` feed.
4. jobs should remain visible through the dedicated `/jobs` surface and jobs feed only.

## Recommendation for next session

Next source file in the fixed order:

- `docs/MODERATION_POLICY.md`

Reason:

- moderation is already a key dependency for the recommended raw-vote-first launch posture
- the next review should confirm that moderation rules line up with ranking protection, flag handling, and ingestion approval
