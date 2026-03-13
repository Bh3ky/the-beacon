
# SERVICE_BOUNDARIES.md

## Project
**Working name:** RiftHub  
**System type:** Community-ranked discussion and discovery platform for African tech

---

# 1. Purpose

This document defines the internal service boundaries of the platform.

The system is intentionally being built as a modular monolith with workers, not as a microservice fleet. Even so, internal boundaries still matter.

This document exists to answer:

- what modules own which responsibilities
- which module is allowed to modify which data
- how cross-module interaction should work
- where future extraction into separate services would make sense

Without clear boundaries, even a monolith becomes messy quickly.

---

# 2. Boundary Philosophy

A good module boundary should do three things:

1. define ownership
2. reduce accidental coupling
3. make future extraction possible if needed

The platform should be designed so that modules are:

- cohesive internally
- loosely coupled externally
- explicit about data ownership

---

# 3. Core Internal Domains

The platform should be split into the following primary domains:

1. identity
2. users
3. posts
4. comments
5. votes
6. feeds
7. ranking
8. moderation
9. ingestion
10. domains/sources
11. admin/operations

These are logical domains, not separate deployed services.

---

# 4. Boundary Rule of Thumb

Each module should own:

- its own business rules
- its own validation rules beyond generic request validation
- writes to its primary tables
- outward-facing service functions

Other modules should depend on service interfaces, not raw implementation details.

---

# 5. Identity Domain

## 5.1 Purpose

Own authentication and session-related concerns.

## 5.2 Responsibilities

- register user
- login/logout
- current session resolution
- password hashing/verification
- session creation/invalidation
- CSRF/session bootstrap helpers
- role resolution helpers

## 5.3 Owns

- `user_sessions` and auth/session models if local
- auth-related service code
- password policy

## 5.4 Does not own

- public profile display rules
- karma
- moderation sanctions logic

Those belong elsewhere.

---

# 6. Users Domain

## 6.1 Purpose

Own user profile and user-facing account state.

## 6.2 Responsibilities

- public user profile retrieval
- profile updates
- user activity summaries
- public user stats
- user status reading

## 6.3 Owns

- `users` table as a profile/account entity
- profile serialization
- public user page logic

## 6.4 Shared concerns

Moderation may change `user.status`, but should do so through a moderation-owned workflow, not direct random mutation from arbitrary modules.

---

# 7. Posts Domain

## 7.1 Purpose

Own all top-level submissions.

## 7.2 Responsibilities

- create post
- validate post payload by `post_type`
- normalize title/slug basics
- resolve post visibility state
- retrieve post details
- post edit rules
- post delete/remove semantics for non-moderation paths

## 7.3 Owns

- `posts` table write logic
- post creation transaction
- post retrieval APIs

## 7.4 Does not own

- vote state mutations
- ranking formula
- moderation sanction logic
- ingestion polling

Those belong to votes, ranking, moderation, and ingestion domains respectively.

---

# 8. Comments Domain

## 8.1 Purpose

Own threaded discussion objects.

## 8.2 Responsibilities

- create comments
- validate comment nesting
- enforce max depth
- update comment content
- remove comment through normal user flows
- serialize flat comment payloads

## 8.3 Owns

- `comments` table write logic
- thread structure rules
- comment retrieval

## 8.4 Does not own

- comment vote calculations
- post feed ranking decisions
- moderation enforcement policy

---

# 9. Votes Domain

## 9.1 Purpose

Own vote state transitions.

## 9.2 Responsibilities

- create/update/remove post votes
- create/update/remove comment votes
- enforce one-vote-per-user-per-target
- enforce self-vote restrictions if enabled
- maintain aggregate counts transactionally
- emit ranking refresh triggers

## 9.3 Owns

- `post_votes`
- `comment_votes`
- vote aggregate update logic

## 9.4 Important boundary rule

No other module should write directly to vote tables.

If a future feature wants to “simulate” or “seed” votes, it should still go through a controlled votes-domain path.

---

# 10. Feeds Domain

## 10.1 Purpose

Own feed assembly and feed querying.

## 10.2 Responsibilities

- top feed retrieval
- new feed retrieval
- ask/show/jobs feed retrieval
- cursor generation/parsing
- feed cache integration
- feed eligibility filtering

## 10.3 Owns

- feed query orchestration
- feed cache key construction
- feed response shaping

## 10.4 Depends on

- ranking domain for score semantics
- posts domain for core post data
- cache layer for snapshots

Feeds domain should not invent its own ranking math independently.

---

# 11. Ranking Domain

## 11.1 Purpose

Own rank score computation and ranking configuration.

## 11.2 Responsibilities

- compute post `rank_score`
- compute comment `rank_score`
- apply category modifiers
- apply domain trust modifiers
- define gravity and decay behavior
- determine score refresh policy

## 11.3 Owns

- ranking formulas
- ranking configuration
- score recomputation jobs

## 11.4 Does not own

- feed eligibility
- moderation state
- ingestion source polling

It computes scores; it does not decide all business visibility rules by itself.

---

# 12. Moderation Domain

## 12.1 Purpose

Own enforcement, sanctions, and content-state transitions due to policy.

## 12.2 Responsibilities

- review flags
- hide/remove/lock posts
- hide/remove comments
- suspend/ban users
- reclassify posts
- block/unblock domains
- moderation audit logging
- decision explanations

## 12.3 Owns

- `flags`
- `moderation_actions`
- moderation workflows
- sanctioned status transitions

## 12.4 Important rule

If a post or comment changes status due to policy, the action should originate from moderation domain, even if another domain requested review.

This preserves auditability.

---

# 13. Ingestion Domain

## 13.1 Purpose

Own external content discovery and publish pipeline.

## 13.2 Responsibilities

- source polling
- parsing external feed data
- normalization
- deduplication orchestration
- ingestion item staging
- auto-publish or review gating
- publish approved ingestion items into posts domain

## 13.3 Owns

- `sources`
- `ingestion_items`
- ingestion worker flows

## 13.4 Important boundary rule

The ingestion domain does **not** own published posts after creation.

Once an ingestion item is approved and converted into a post, the resulting post belongs to posts domain like any other post.

---

# 14. Domains/Sources Domain

This can remain inside ingestion initially, but conceptually it is worth separating.

## 14.1 Purpose

Own source/domain trust metadata.

## 14.2 Responsibilities

- canonical host tracking
- trust score updates
- block/unblock domain state
- source metadata maintenance

## 14.3 Owns

- `domains`
- possibly source trust policy shared with ingestion/moderation

In MVP, this may stay grouped with ingestion and moderation coordination.

---

# 15. Admin/Operations Domain

## 15.1 Purpose

Own internal operational surfaces.

## 15.2 Responsibilities

- source management UI/API
- ingestion run controls
- health dashboards
- operational metrics views
- maintenance controls

## 15.3 Important note

Admin/operations does not own business rules. It exposes controlled ways to interact with other domains.

---

# 16. Cross-Domain Interaction Rules

The system should use service-layer calls between domains.

Examples:

- comments domain creates comment → ranking domain notified for score refresh
- votes domain updates vote → ranking domain notified → feeds domain cache invalidated
- moderation domain removes post → feeds domain cache invalidated
- ingestion domain publishes item → posts domain creates post → ranking domain seeds score

This keeps ownership clear.

---

# 17. Event-Like Internal Triggers

Even inside a monolith, it is useful to think in internal event terms.

Examples:

- `post_created`
- `post_updated`
- `post_removed`
- `comment_created`
- `vote_changed`
- `domain_blocked`
- `ingestion_item_published`

These do not need a full event bus at first. Simple service calls or task enqueue patterns are enough.

The important point is conceptual decoupling.

---

# 18. Data Ownership Matrix

| Table / Resource | Owning Domain |
|---|---|
| users | users / identity shared |
| `user_sessions` / session records | identity |
| posts | posts |
| comments | comments |
| post_votes | votes |
| comment_votes | votes |
| flags | moderation |
| moderation_actions | moderation |
| domains | ingestion implementation owner with moderation-authorized mutation paths |
| sources | ingestion |
| ingestion_items | ingestion |

Where ownership is shared conceptually, one implementation owner must still be chosen to avoid ambiguity.

Recommended choice:

- `domains` operational ownership sits with moderation + ingestion coordination, but implementation can live under ingestion services with moderation-authorized mutation paths.

---

# 19. Boundary Violations to Avoid

These are common failure modes.

## 19.1 Feed routes writing ranking logic inline

Bad pattern:

- feed endpoint directly calculates scores ad hoc

Why bad:

- duplicates ranking logic
- creates inconsistent ordering

---

## 19.2 Moderation routes mutating posts without audit logging

Bad pattern:

- direct status update with no moderation action record

Why bad:

- destroys auditability

---

## 19.3 Ingestion creating posts through raw model writes

Bad pattern:

- ingestion worker inserts directly into `posts` table without post-domain service

Why bad:

- bypasses validation
- creates inconsistency with user-created posts

---

## 19.4 Votes updating counts outside transactions

Bad pattern:

- write vote row first, update aggregates later without integrity safeguards

Why bad:

- causes drift and race conditions

---

# 20. Future Extraction Boundaries

If the system grows substantially, some domains could become separate services.

Most likely extraction order:

## 20.1 Ingestion service
Natural candidate because:

- scheduled and batch-heavy
- externally facing to publishers/feeds
- operationally distinct from user request paths

## 20.2 Search/analytics service
Natural candidate later, if search and trend analysis become large.

## 20.3 Notification service
Useful only once real notification complexity exists.

The core posts/comments/votes/moderation stack should remain together for a long time.

---

# 21. Team Ownership Model

If the project eventually has multiple developers, boundaries help assign ownership.

Suggested ownership mapping:

| Domain | Likely primary owner |
|---|---|
| frontend surfaces | frontend/product engineer |
| API and posts/comments/votes | backend engineer |
| ranking/feeds | backend/product systems engineer |
| ingestion/ops | backend/platform engineer |
| moderation/admin surfaces | backend + product collaboration |

Early on, one founder may own all of this, but the boundaries still help avoid mental sprawl.

---

# 22. Boundary-Aware Testing Strategy

Each domain should have its own test emphasis.

## Identity
- auth flows
- session handling
- password rules

## Posts
- post type validation
- duplicate handling path integration
- edit/delete constraints

## Comments
- nesting depth
- parent-child consistency

## Votes
- uniqueness
- toggle behavior
- aggregate correctness

## Ranking
- score formula correctness
- decay behavior
- category/domain modifiers

## Feeds
- ordering correctness
- cursor behavior
- hidden/removed exclusion

## Moderation
- action logging
- status transitions
- permission checks

## Ingestion
- normalization
- dedupe
- publish/reject flow

---

# 23. Practical Implementation Rule

When writing code, ask:

1. Which domain owns this rule?
2. Which domain owns the write?
3. Which other domains need to react?

If those answers are unclear, the code probably belongs in the wrong place.

---

# 24. Summary

The platform should be built as a modular monolith with clear internal boundaries.

The key domain owners are:

- identity
- users
- posts
- comments
- votes
- feeds
- ranking
- moderation
- ingestion

The most important architectural discipline is this:

- **ownership of rules**
- **ownership of writes**
- **clear reaction paths**

That discipline keeps the codebase coherent now and makes future scaling or extraction possible later without rewriting the entire system.
