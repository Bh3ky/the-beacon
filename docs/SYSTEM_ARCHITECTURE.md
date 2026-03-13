# SYSTEM_ARCHITECTURE.md

## Project
**Working name:** RiftHub  
**System type:** Community-ranked discussion and discovery platform for African tech

---

# 1. Purpose

This document defines the runtime system architecture of the platform.

While the previous documents define:

- data model
- API contracts
- ranking logic
- ingestion behavior
- moderation policy

this document defines **how the system actually runs in production**.

It covers:

- service topology
- request flow
- compute boundaries
- cache strategy
- background workers
- deployment model
- scaling paths
- failure boundaries

The goal is to produce a system that is:

- simple enough for early-stage execution
- reliable enough for public launch
- modular enough to scale without major rewrites

---

# 2. Architecture Philosophy

The platform should start as a **modular monolith with dedicated workers**, not as microservices.

This is the correct choice because:

- the product is still evolving quickly
- ranking, moderation, posts, and ingestion are tightly coupled
- operational simplicity matters more than theoretical scalability
- the expected early traffic does not justify distributed service complexity

So the architecture should be:

- **one frontend application**
- **one backend API application**
- **one or more worker processes**
- **managed database**
- **managed cache**
- **shared observability stack**

This gives the product enough separation where it matters while avoiding premature infrastructure sprawl.

---

# 3. High-Level Topology

```text
Users
  ↓
Next.js Frontend (Vercel)
  ↓
FastAPI Backend API (Railway)
  ↓
PostgreSQL (Supabase)
  ↓
Redis (Upstash)
```

```text
Background Workers (Railway worker service)
  ↙                ↓                 ↘
Ranking Refresh   Ingestion Jobs     Moderation/Housekeeping
```

# 4. Primary System Components

## 4.1 Frontend application

**Technology:** Next.js 15 + TypeScript + Tailwind CSS  
**Hosting:** Vercel

**Responsibilities**

- render feed pages
- render post detail pages
- render submission flows
- manage user session state
- call backend APIs
- perform optimistic UI updates for voting where appropriate
- present moderation and admin UI for authorized users

The frontend should remain thin. It is a rendering and interaction layer, not the source of business logic.

## 4.2 Backend API service

**Technology:** FastAPI + SQLAlchemy async + Alembic  
**Hosting:** Railway

**Responsibilities**

- auth and authorization
- API request validation
- domain business logic
- read and write access to Postgres
- cache reads and writes
- vote processing
- comment processing
- feed queries
- moderation actions
- ingestion admin actions

The backend API is the system’s primary control plane.

## 4.3 Database

**Technology:** PostgreSQL via Supabase

**Responsibilities**

- system of record
- transactional data integrity
- relational queries
- persistence for users, posts, comments, votes, moderation, sources, and ingestion items

Postgres is the source of truth for all durable state.

## 4.4 Cache layer

**Technology:** Redis via Upstash

**Responsibilities**

- feed snapshots
- hot post metadata
- rate limiting counters
- temporary ranking caches
- worker locks
- dedupe helper keys

Redis exists to accelerate hot reads and lightweight coordination, not to replace the database.

## 4.5 Background worker service

**Technology:** Python worker process on Railway

**Responsibilities**

- score recomputation
- feed cache refresh
- ingestion polling
- ingestion normalization and publishing
- periodic reconciliation jobs
- stale cleanup
- optional notification jobs later

Workers should be independently deployable from the API service.

# 5. Deployment Model

## 5.1 Environments

The system should have at least three environments:

- development
- staging
- production

Each environment should have:

- separate API config
- separate database
- separate Redis namespace or instance
- separate secrets
- separate frontend deployment target if practical

Never mix staging and production credentials or data.

## 5.2 Frontend deployment

Vercel handles:

- preview deployments per branch
- production deployment on the main branch
- environment variables per environment
- asset optimization and CDN distribution

## 5.3 Backend deployment

Railway handles:

- API deployment
- worker deployment
- environment management
- restart policies
- logs

The API and worker should be separate Railway services.

## 5.4 Managed infrastructure

Use managed services where possible:

| Component | Provider |
| --- | --- |
| frontend hosting | Vercel |
| backend hosting | Railway |
| database | Supabase |
| cache | Upstash |

This reduces ops overhead and is appropriate for an early-stage product.

# 6. Network and Trust Boundaries

The system has several trust boundaries.

## 6.1 Public boundary

The frontend is public.

Anyone can:

- load feed pages
- browse posts
- view comments
- access public user pages

## 6.2 Authenticated user boundary

Authenticated users can additionally:

- submit posts
- vote
- comment
- flag content

For v1, authenticated browser access assumes:

- an HTTP-only cookie session
- CSRF enforcement on state-changing routes
- explicit allowed origins for credentialed cross-origin requests

## 6.3 Moderator and admin boundary

Moderators and admins can access:

- moderation queue
- ingestion review tools
- source management
- user sanctions
- domain controls

These routes require strict role enforcement.

## 6.4 Internal worker boundary

Workers are not public-facing. They should communicate with:

- Postgres
- Redis
- optionally internal API services if needed

They should not expose public HTTP surfaces unless there is a strong operational need.

# 7. Core Request Flows

## 7.1 Feed read flow

When a user loads the homepage:

```text
Browser
  ↓
Next.js route/page
  ↓
Backend API: GET /feeds/top
  ↓
Redis feed snapshot lookup
  ↓
if hit → return ordered items
if miss → query Postgres, compute/assemble feed, write Redis, return
```

**Design goal**

Homepage latency should be dominated by cached reads wherever possible.

## 7.2 Post detail flow

When a user opens a post page:

```text
Browser
  ↓
Next.js page
  ↓
Backend API: GET /posts/{id}/{slug}
  ↓
Postgres fetch post + author + domain + viewer state
  ↓
Backend API: GET /posts/{id}/comments
  ↓
Postgres fetch comments
  ↓
frontend reconstructs thread tree
```

This can optionally be partially cached for hot posts.

## 7.3 Submit post flow

```text
Authenticated user
  ↓
Frontend submit form
  ↓
Backend API: POST /posts
  ↓
validate payload
  ↓
normalize URL if present
  ↓
dedupe check
  ↓
write post row
  ↓
enqueue/trigger score refresh
  ↓
invalidate feed caches
  ↓
return created post
```

## 7.4 Vote flow

```text
Authenticated user
  ↓
Frontend vote action
  ↓
Backend API: POST /posts/{id}/vote
  ↓
validate permission and rate limits
  ↓
upsert vote row
  ↓
update aggregates
  ↓
recompute rank or enqueue recompute
  ↓
invalidate relevant caches
  ↓
return updated vote state
```

Votes are high-frequency operations and must remain cheap.

## 7.5 Ingestion flow

```text
Scheduler
  ↓
Worker selects due sources
  ↓
fetch source content
  ↓
parse items
  ↓
normalize URLs/titles/dates
  ↓
dedupe check
  ↓
classify
  ↓
auto-publish or moderation queue
  ↓
create post if approved
  ↓
invalidate feed caches
```

# 8. Internal Module Layout

Even though the backend is deployed as a single API service, it should be internally modular.

**Suggested backend package layout**

```text
backend/
  app/
    api/
      routes/
    core/
      config.py
      security.py
      logging.py
    db/
      base.py
      session.py
      models/
    schemas/
    services/
      auth/
      users/
      posts/
      comments/
      votes/
      feeds/
      ranking/
      moderation/
      ingestion/
    workers/
    utils/
```

This structure allows clean boundaries without service explosion.

# 9. Frontend Architecture

**Suggested frontend structure**

```text
frontend/
  app/
    (public)/
      page.tsx
      new/
      ask/
      show/
      jobs/
      post/[id]/[slug]/
      user/[username]/
    (auth)/
      login/
      register/
    (dashboard)/
      moderation/
      admin/
  components/
    layout/
    feed/
    post/
    comments/
    forms/
    moderation/
  lib/
    api/
    auth/
    utils/
    types/
```

The frontend should be organized around product surfaces, not generic UI buckets alone.

# 10. Cache Strategy

Redis is important, but it should remain scoped and disciplined.

## 10.1 What should be cached

**Feed snapshots**

**Examples**

```text
feed:top
feed:new
feed:ask
feed:show
feed:jobs
```

These keys store ordered IDs and optionally hydrated lightweight metadata.

**Hot post metadata**

**Examples**

```text
post:{id}:summary
post:{id}:viewer:{user_id}
```

Only cache where the read pattern justifies it, and scope per-viewer cache carefully.

**Comment tree cache**

**Examples**

```text
post:{id}:comments
```

Useful for very active posts, but TTLs should remain short.

**Rate limits**

**Examples**

```text
rate:vote:{user_id}
rate:submit:{user_id}
rate:login:{ip}
```

**Worker locks**

**Examples**

```text
lock:source:{source_id}
lock:feed_refresh:top
```

These prevent duplicate job execution.

## 10.2 What should not be cached aggressively

Do not heavily cache:

- user moderation state without invalidation discipline
- private auth-sensitive objects
- large mutable admin datasets
- anything requiring complex per-user coherence unless truly necessary

## 10.3 Cache TTL guidelines

| Key type | TTL |
| --- | --- |
| top feed | 30 to 120 sec |
| new feed | 30 sec |
| ask/show feed | 60 sec |
| jobs feed | 2 to 10 min |
| post summary | 60 sec |
| comment tree | 30 to 60 sec |
| rate limit keys | policy-defined |

# 11. Database Access Pattern

The database remains the source of truth.

## 11.1 General rule

Use Postgres for:

- writes
- transactional reads
- moderation history
- ingestion records
- canonical feed assembly when cache misses occur

Redis should never become the sole authority for business-critical state.

## 11.2 ORM usage

Use SQLAlchemy async models for:

- transactional integrity
- explicit relationships
- service-layer queries

Complex feed queries may use hand-tuned SQL when needed.

## 11.3 Migration model

Alembic must control all schema changes.

Rules:

- no manual production schema drift
- every DB change in a versioned migration
- stage migrations before production rollout

# 12. Worker Architecture

The worker service is central to reliability.

## 12.1 Why separate workers exist

Workers isolate slow or recurring tasks from the user-facing request path.

This protects API latency.

## 12.2 Worker job categories

**Ingestion jobs**

- poll sources
- parse feeds
- write ingestion items
- publish approved content

**Ranking jobs**

- recompute hot post scores
- refresh feed snapshots
- recalculate comment scores if needed

**Reconciliation jobs**

- repair counter drift
- reindex stale content
- expire old job posts
- clear obsolete caches

**Moderation support jobs**

- aggregate suspicious signals
- batch-scan low-trust content
- identify spam patterns later

## 12.3 Execution model

At MVP stage, a simple polling worker loop or lightweight task runner is sufficient.

Avoid bringing in heavy queue systems unless job volume justifies it.

Acceptable patterns:

- scheduled polling loop
- Redis-backed lightweight task queue
- cron-triggered internal runner

The exact mechanism matters less than keeping the interfaces clean.

# 13. Scheduling Model

The system needs scheduled recurring tasks.

## 13.1 Required scheduled jobs

| Job | Frequency |
| --- | --- |
| source polling | every few minutes |
| top feed refresh | every 30 to 120 sec |
| comment/post score refresh | every few minutes |
| expired job cleanup | hourly |
| stale cache cleanup | hourly or daily |
| aggregate reconciliation | daily |

## 13.2 Scheduler placement

Recommended options:

- worker process with internal scheduler
- platform cron triggering a worker command or a private internal endpoint behind platform controls

Do not overload the API service with internal scheduling logic if it can be avoided.

# 14. Observability Architecture

The system must be observable from day one.

## 14.1 Logs

All services should emit structured logs.

Log categories:

- API requests
- auth failures
- moderation actions
- ingestion failures
- worker failures
- ranking recomputation anomalies

## 14.2 Metrics

Track at minimum:

- API latency by route
- DB query latency
- cache hit rate
- ingestion success and failure count
- feed refresh duration
- worker job duration
- error rate
- moderation queue size

## 14.3 Error tracking

Use centralized error monitoring for:

- frontend exceptions
- backend exceptions
- worker crashes

This is essential because worker failures can otherwise silently degrade the platform.

# 15. Security Architecture

Security must be built into the system boundary design.

## 15.1 Secret management

All secrets should be environment-managed:

- DB URL
- Redis URL
- auth secrets
- admin credentials
- external API keys if added later

Secrets must never be committed.

## 15.2 Auth boundary

The API must validate auth on every protected route.

Role checks must happen server-side, never only in the frontend.

For v1 session auth:

- use an `HttpOnly`, `Secure` session cookie
- use `SameSite=Lax` or `SameSite=Strict` where possible
- require CSRF validation on mutating routes
- validate request origin for state-changing requests
- if frontend and API are cross-origin, enable credentialed CORS only for explicit allowlisted origins

## 15.3 Input safety

All user-generated text and ingested external text must be sanitized appropriately before rendering.

Important surfaces:

- markdown rendering
- comments
- profile bios
- ingestion titles and summaries

## 15.4 Internal action safety

Sensitive operations should be protected by:

- role-based access
- audit logs
- rate limits where appropriate

**Examples**

- source creation
- user bans
- domain blocks
- ingestion publish and reject actions

# 16. Failure Modes and Resilience

The system must remain usable when individual components degrade.

## 16.1 Redis unavailable

If Redis fails:

- feed requests may fall back to Postgres
- rate limits may degrade
- snapshot refresh may slow down

The site should remain functional, though slower.

Redis should be treated as an accelerator, not a requirement for correctness.

## 16.2 Worker unavailable

If workers fail:

- ingestion pauses
- ranking freshness degrades
- feed caches may become stale

The site can still serve existing content, but freshness suffers.

This is acceptable short term, but it must alert operators.

## 16.3 Postgres unavailable

If Postgres is unavailable:

- the core product is unavailable

This is the most critical dependency and should be treated accordingly.

## 16.4 Frontend unavailable

If the frontend deployment fails but the backend is healthy:

- APIs may remain accessible
- the user-facing product is functionally degraded

## 16.5 Backend unavailable

If the API is down:

- the frontend cannot load dynamic content
- voting, submission, and commenting stop

# 17. Scaling Strategy

The architecture should scale incrementally.

## 17.1 Early-stage scaling

Scale in this order:

- optimize queries
- increase cache effectiveness
- scale API horizontally
- scale workers separately
- move expensive jobs out of hot paths

This will likely be enough for a long time.

## 17.2 Horizontal scaling

**Frontend**

Vercel handles this automatically.

**API**

Railway services can scale horizontally if needed.

**Workers**

Multiple worker instances can process jobs if locking and idempotency are handled correctly.

## 17.3 Database scaling

Most likely scaling path:

- tune indexes
- tune slow queries
- optimize write patterns
- only later consider replicas or heavier scaling

Do not optimize for extreme scale prematurely.

# 18. Data Flow by Product Surface

## 18.1 Homepage

**Dependencies**

- feed snapshot cache
- post metadata query path
- ranking refresh worker

**Critical properties**

- fast
- stable
- cache-friendly

## 18.2 Post detail pages

**Dependencies**

- post read path
- comment retrieval path
- vote state resolution

**Critical properties**

- correct thread rendering
- moderate freshness
- acceptable performance on active posts

## 18.3 Submission flow

**Dependencies**

- auth
- URL normalization
- dedupe logic
- DB write integrity

**Critical properties**

- correctness over speed
- strong validation
- clear duplicate response behavior

## 18.4 Moderation UI

**Dependencies**

- role-aware auth
- flags queries
- moderation action logging
- source and domain control flows

**Critical properties**

- correctness
- auditability
- low accidental-action risk

## 18.5 Ingestion admin

**Dependencies**

- sources table
- ingestion item staging
- worker state visibility

**Critical properties**

- operational clarity
- safe approval and rejection workflow
- source health monitoring

# 19. API and Worker Separation Rule

A good design rule:

- user-driven synchronous actions go through the API
- slow, recurring, or bulk actions go through workers

**Examples**

| Action | Owner |
| --- | --- |
| create comment | API |
| vote on post | API |
| refresh top feed | worker |
| poll RSS sources | worker |
| recompute old post scores | worker |
| reconcile counters | worker |

This separation keeps request latency predictable.

# 20. Recommended Runtime Configuration

The following should be configuration-driven:

- ranking gravity
- feed cache TTLs
- source poll intervals
- repost window
- comment max depth
- post and comment edit window
- job expiry duration
- rate limits
- trusted source thresholds

These values should not be deeply hardcoded in multiple services.

# 21. Suggested Production Readiness Checklist

Before public launch, the system should satisfy:

- staging environment exists
- migrations tested in staging
- feed cache behavior verified
- duplicate URL normalization verified
- worker restarts handled cleanly
- moderation logging verified
- auth and role checks verified
- CSRF and cross-origin cookie behavior verified
- source polling failure alerts configured
- error monitoring enabled
- basic backups confirmed

# 22. Future Evolution Path

The current architecture should survive well beyond MVP.

Future additions can include:

- dedicated search service
- analytics pipeline
- notification service
- recommendation service
- read replicas
- separate ingestion service if volume warrants

None of these should be added until the existing modular monolith becomes a real bottleneck.

# 23. Summary

The recommended production system architecture is:

- Next.js frontend on Vercel
- FastAPI backend on Railway
- Postgres on Supabase
- Redis on Upstash
- separate worker service for ingestion, ranking, and maintenance

This design is intentionally conservative.

It optimizes for:

- fast iteration
- low ops overhead
- clean product boundaries
- safe scaling
- strong alignment with the platform’s actual needs

The most important architectural principle is that the product should remain simple at the deployment level while modular at the code level. That balance gives the project the best chance of moving quickly without collapsing into technical confusion.
