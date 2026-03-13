# Qs.md

## Purpose

This file tracks product and implementation questions discovered during planning.

It should distinguish clearly between:

- resolved decisions
- still-open questions

It should not remain a second source of truth once an item is resolved elsewhere.

## Resolved Decisions

### Product and behavior

| Question | Decision |
| --- | --- |
| Are downvotes enabled for users in v1? | No. V1 is upvote-only. |
| Are posts editable after submission, and for how long? | Yes. Posts are editable for `15 minutes`. |
| Are comments editable after submission, and for how long? | Yes. Comments are editable for `15 minutes`. |
| Are reposts of old links allowed after a time window? | Yes. Link reposts are allowed after `30 days`. |
| Will jobs expire automatically? | Yes. Jobs expire after `30 days`. |
| Will ingested content be clearly labeled as system-imported? | Yes. Ingested content should carry source attribution. |
| Is moderator approval required for new users' first submissions? | New users' first `1-3` submissions may go through stricter anti-spam checks. |
| What is the ranking direction at launch? | Use the ranking model in `RANKING_SYSTEM.md`: raw vote counts only in v1, lower-gravity hot ranking for non-job feeds, and separate recency-first logic for jobs. |
| Should `show` be a post type? | No. `show` is a category, not a post type. |
| Are job posts part of the first MVP? | Yes, but only through the dedicated jobs surface, not the main `top` feed. |

### Auth and security

| Question | Decision |
| --- | --- |
| What auth mode should v1 use? | HTTP-only cookie sessions. |
| How should CSRF be handled? | Session-based CSRF protection with frontend memory-only token storage, auto-attached on mutating requests, plus origin validation. |

### Ingestion and moderation

| Question | Decision |
| --- | --- |
| Should any sources auto-publish at MVP launch? | No. MVP launch is review-first for all sources. |
| How are blocked sources represented? | Operationally as `status = disabled`. |
| Are moderation appeals in-product for MVP? | No. Appeals are manual/out-of-band at launch. |
| Are moderator warnings a first-class action in MVP? | No. Warnings remain communication plus moderator notes only. |

## Still-Open Questions

### Ingestion

1. What is the actual first approved source list for launch?

### Data-model implementation details

1. Should usernames be case-insensitive at the DB layer via `citext`?
2. Should email verification state be stored on `users`, or delegated fully to the auth layer/provider?
3. Should downvotes exist internally from day one even if hidden in the UI?
4. Should repost rules be enforced by a partial unique index, solely in application logic, or both?
5. Should karma be fully derived or stored eagerly?
6. Do we want bookmarks in MVP or later?
7. Is `view_count` worth storing in MVP, or should it be deferred?
8. Should source trust and domain trust remain separate concepts as currently modeled?

## Usage Rule

When an item here is resolved:

1. update the relevant source-of-truth document
2. update `docs/agent-review/MEMORY.md`
3. move the item from `Still-Open Questions` to `Resolved Decisions` or remove it if redundant
