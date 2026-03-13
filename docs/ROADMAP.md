# ROADMAP.md

## Project
**Working name:** RiftHub  
**System type:** Community-ranked discovery and discussion platform for African tech

---

# 1. Purpose

This document defines the phased build plan for the platform.

The architecture, data model, API contracts, ranking logic, ingestion behavior, and security constraints are already defined across the docs set. This roadmap defines the **implementation order** so the system is built in a way that keeps momentum high and avoids unnecessary rework.

The implementation strategy is a **vertical slice strategy**:

Build a working product loop early, then expand it carefully.

---

# 2. Current Stage

The project is currently in:

## Phase 0: Docs review

The goals of this phase are:

- review each document one at a time
- resolve contradictions between docs
- clean up Markdown structure and syntax
- identify unclear product or implementation decisions
- produce planning notes before coding starts

No production code should be written until the core docs are coherent enough to guide implementation safely.

---

# 3. Core Product Loop

Everything revolves around this loop:

```text
discover → vote → discuss → submit
```

This means the following features must exist before anything else:

- posts
- feeds
- voting
- comments

Without these, the product does not function.

---

# 4. Phase Overview

The build process is divided into phases.

| Phase | Focus |
| --- | --- |
| Phase 0 | Docs review and clarification |
| Phase 1 | Project foundation |
| Phase 2 | Database and core models |
| Phase 3 | Core API |
| Phase 4 | Frontend core |
| Phase 5 | Ranking system |
| Phase 6 | Worker system |
| Phase 7 | Moderation |
| Phase 8 | Ingestion pipeline |
| Phase 9 | Production readiness |

Each phase builds on the previous one.

---

# 5. Phase 1 — Project Foundation

**Goal:** create the repository and development environment.

Reference:

- `REPO_STRUCTURE.md`

## 5.1 Tasks

Create the repository structure defined in the repo structure document.

Initialize:

```text
apps/web
apps/api
apps/worker
docs
```

Set up tooling and shared development conventions.

## 5.2 Frontend setup

Install:

```text
Next.js
TypeScript
Tailwind CSS
shadcn/ui
```

Validation:

- the basic app boots
- one page renders correctly
- local developer workflow is usable

## 5.3 Backend setup

Initialize:

```text
FastAPI
SQLAlchemy async
Alembic
```

Add the basic app structure.

Validation:

- API starts locally
- health endpoint responds
- config loading works

## 5.4 Worker setup

Create a basic worker runner.

Validation:

- worker process starts
- logs output correctly
- can run a simple scheduled or manual task

## 5.5 Local services

Start development services:

```text
Postgres
Redis
```

Use Docker or managed dev instances.

Validation:

- local apps can connect to both services
- environment setup is documented

---

# 6. Phase 2 — Database Models

**Goal:** define persistent data structures.

Reference:

- `DATABASE_SCHEMA.md`

Implement models for:

```text
users
posts
comments
post_votes
comment_votes
domains
sources
ingestion_items
flags
moderation_actions
```

## 6.1 Tasks

- create SQLAlchemy models
- create Alembic migrations
- apply migrations to the development database

## 6.2 Validation

Confirm:

- tables are created
- relationships are valid
- indexes are applied
- enums and constraints match the schema doc

---

# 7. Phase 3 — Core API

**Goal:** build the minimal API for the core product loop.

Reference:

- `API_SPEC.md`

## 7.1 Implement APIs

### Auth

```http
POST /auth/register
POST /auth/login
GET /auth/me
```

### Posts

```http
POST /posts
GET /posts/{post_id}
```

### Comments

```http
POST /posts/{post_id}/comments
GET /posts/{post_id}/comments
```

### Votes

```http
POST /posts/{post_id}/vote
POST /comments/{comment_id}/vote
```

### Feeds

```http
GET /feeds/top
GET /feeds/new
GET /feeds/jobs
```

## 7.2 Validation

Use Postman, `curl`, or automated API tests to confirm the endpoints behave correctly.

At this stage the platform should function entirely through the API.

Auth for v1 should use HTTP-only cookie sessions with:

- `HttpOnly`
- `Secure`
- `SameSite=Lax` or `SameSite=Strict` where possible
- server-side session validation or a signed session token
- CSRF protection for state-changing requests

---

# 8. Phase 4 — Frontend Core

**Goal:** create the usable web interface.

## 8.1 Build pages

Homepage:

```text
/ → top feed
```

New feed:

```text
/new
```

Post page:

```text
/post/{id}/{slug}
```

Jobs feed:

```text
/jobs
```

User profile:

```text
/user/{username}
```

## 8.2 Implement UI components

Feed item should show:

- title
- domain
- vote count
- comment count
- timestamp

Also implement:

- voting UI
- comment threads
- submission form
- visible jobs surface in the MVP UI

## 8.3 Validation

You should now have a fully usable platform without ingestion.

Users should be able to:

- register
- submit posts
- vote
- comment
- browse feeds

This is the first real product milestone.

---

# 9. Phase 5 — Ranking System

**Goal:** implement the ranking algorithm.

Reference:

- `RANKING_SYSTEM.md`

## 9.1 Tasks

- implement the base hot-score model from the ranking document
- store `rank_score` in the database
- recalculate scores on vote and comment changes
- add periodic recalculation for active posts

Do not invent a separate formula here. The implementation must align with the ranking document.

## 9.2 Feed query behavior

Feeds should order by:

```sql
rank_score DESC
```

With deterministic tie-breakers defined in the ranking doc.

## 9.3 Validation

Test scenarios:

- newer strong posts can outrank older weak posts
- higher-quality engagement outranks low engagement
- aging reduces rank over time
- category-specific feeds still behave correctly

Feed quality should now resemble the intended hot-ranking model.

---

# 10. Phase 6 — Worker System

**Goal:** introduce background jobs.

Workers handle:

- score refresh
- feed cache refresh
- maintenance tasks

## 10.1 Implement jobs

```text
refresh_post_scores
refresh_feed_snapshots
reconcile_vote_counts
expire_job_posts
```

## 10.2 Scheduling

Run jobs periodically.

Example intervals:

```text
ranking refresh → every minute
maintenance → hourly
```

Validation:

- scheduled jobs run reliably
- duplicate executions are controlled
- failures are observable

---

# 11. Phase 7 — Moderation

**Goal:** protect community quality early enough to test and tune moderation during MVP development.

Reference:

- `MODERATION_POLICY.md`

## 11.1 Implement

Flagging:

```http
POST /flags
```

Moderation actions:

- remove post
- remove comment
- suspend user
- ban user

## 11.2 Moderator dashboard

Minimal UI:

- flag queue
- moderation actions

## 11.3 Validation

Confirm:

- moderator actions are auditable
- role checks are enforced
- moderation flows cannot be triggered by normal users
- moderation can be exercised during MVP testing, not added after the fact

---

# 12. Phase 8 — Ingestion Pipeline

**Goal:** automatically populate the platform.

Reference:

- `INGESTION_PIPELINE.md`

## 12.1 Tasks

Implement source polling.

Steps:

```text
fetch RSS
parse feed
normalize URLs
dedupe
store ingestion items
publish as posts
```

## 12.2 Add sources

Start with a real approved source list, not placeholders.

The exact approved list should be defined during Phase 0 and then implemented here.

Initial candidates currently mentioned:

- TechCabal
- TechCrunch Africa
- Rest of World

## 12.3 Validation

Confirm:

- new articles appear in the feed
- duplicates are prevented
- source failures are visible

This prevents empty feeds and supports the cold-start strategy.

---

# 13. Phase 9 — Production Readiness

**Goal:** deploy and stabilize.

References:

- `SYSTEM_ARCHITECTURE.md`
- `SECURITY.md`
- `TESTING_STRATEGY.md`

## 13.1 Tasks

Deploy:

```text
Vercel   → frontend
Railway  → API
Railway  → worker
Supabase → database
Upstash  → Redis
```

## 13.2 Add monitoring

Enable:

- logs
- error tracking
- health checks

## 13.3 Run tests

Execute:

- unit tests
- integration tests
- end-to-end tests

---

# 14. Launch Checklist

Before launch, confirm:

- ranking works
- feeds load quickly
- ingestion populates the site
- spam protection is active
- moderation is working
- deployment is stable

---

# 15. Post-Launch Improvements

After launch, consider adding:

- search
- notifications
- user following
- improved reputation system
- analytics dashboards
- mobile UI improvements

These should not delay MVP.

---

# 16. Summary

The correct build order is:

```text
docs review
→ foundation
→ database
→ API
→ frontend
→ ranking
→ workers
→ moderation
→ ingestion
→ production readiness
```

This order ensures that the core product loop works early.

Once that loop functions, the platform can evolve into a larger ecosystem intelligence product without forcing premature complexity into the first build.
