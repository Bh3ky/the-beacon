# PHASE3_CORE_API_PLAN.md

## Purpose

This file defines the **final execution plan** for **Phase 3: Core API** after Phase 2 database and migration validation completed successfully.

This is the implementation-ready planning note for the phase. It captures the decisions that are now locked before coding starts.

---

## Source Documents

This plan is based on:

- [ROADMAP.md](/Users/telasi/Developer/RiftHub/docs/ROADMAP.md)
- [API_SPEC.md](/Users/telasi/Developer/RiftHub/docs/API_SPEC.md)
- [SERVICE_BOUNDARIES.md](/Users/telasi/Developer/RiftHub/docs/SERVICE_BOUNDARIES.md)
- [DEVELOPMENT_TEST_CHECKPOINTS.md](/Users/telasi/Developer/RiftHub/docs/agent-review/DEVELOPMENT_TEST_CHECKPOINTS.md)

---

## Preconditions

Phase 2 is treated as complete for planning purposes:

- database models reviewed and tightened
- Alembic initial revision synced to current models
- focused API/backend test suite passing
- local manual validation completed:
  - migration upgrade
  - downgrade
  - re-upgrade
  - schema inspection
  - enum/index validation
  - manual bad-data checks
  - API startup and `/health` validation

---

## Important Context

`ROADMAP.md` still says the project is in `Phase 0: Docs review`.

That line is now stale. For Phase 3 work, the authoritative part of the roadmap is the **Phase 3 section**, not the old current-stage marker.

---

## Phase 3 Goal

Build the minimum HTTP API needed for the core product loop:

```text
discover -> vote -> discuss -> submit
```

The API should be usable through HTTP alone, without frontend-specific shortcuts or direct database access.

---

## Boundary Rules For Phase 3

These rules are locked unless explicitly revised in the docs first:

1. Route handlers stay thin.
   Business rules belong in domain service code, not FastAPI endpoints.

2. Identity/auth owns session behavior.
   Session creation, invalidation, cookie handling, CSRF helpers, and current-user resolution belong to the identity domain.

3. Posts, comments, and votes keep their own write logic.
   Cross-domain writes should happen through service functions, not ad hoc ORM usage inside endpoints.

4. The API contract should stay aligned with `API_SPEC.md` unless we deliberately revise the spec first.

5. Phase 3 security is part of the slice, not a later add-on.
   Cookie settings, CSRF behavior, and protected-route enforcement must be implemented with the auth foundation.

---

## Phase 3 Slice Order

### Slice 1: Auth and Session Foundation

Status: **implemented**

Implement first:

- `POST /auth/register`
- `POST /auth/resend-verification`
- `POST /auth/verify`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`

Supporting work included in this slice:

- password hashing and verification
- account verification flow
- dedicated verification-token storage
- verification delivery port and environment-specific delivery adapters
- resend-verification flow for pending accounts
- session creation in `user_sessions`
- session invalidation
- current-session resolution dependency/helper
- secure cookie issuance
- session-bound CSRF token strategy for mutating requests
- origin-validation policy for browser-based state-changing requests
- auth rate limiting

Why first:

- all protected write routes depend on it
- security mistakes here would leak into every later slice
- `SERVICE_BOUNDARIES.md` makes identity/session ownership explicit

Locked direction from review:

- Path B: registration is verification-first
- `POST /auth/register` creates a non-authenticated pending account
- no authenticated session is issued until verification completes
- `POST /auth/verify` completes verification
- `POST /auth/resend-verification` rotates the active pending verification token without creating a session
- verification completion is what creates the session, sets the auth cookie, and sets the CSRF cookie
- verification tokens live in a dedicated auth-owned table rather than `user_sessions`
- verification delivery stays behind a dedicated port and uses a configured frontend base URL
- verification token lifetime is `24 hours`
- emails are canonicalized by trimming and lowercasing the full address before register/login lookup
- login rejects unverified accounts with `403 account_pending_verification`
- logout is idempotent and always returns `204 No Content`
- session model is database-backed opaque tokens with only the token hash stored server-side
- session lifetime uses `30 minutes` idle timeout plus `24 hours` absolute lifetime
- `last_seen_at` updates are throttled to at most once every `10 minutes`
- register/login/verify carry dedicated auth rate limits from the start

Planning consequence:

- this is not just a route-handler detail
- Slice 1 now includes a small schema/spec expansion:
  - user lifecycle must support a pending verification state
  - verification token storage must exist in a dedicated auth table
  - the auth API contract must define the verification completion route and post-verification session issuance behavior

### Slice 2: Read-Only Core Loop Endpoints

Status: **implemented**

Implement next:

- `GET /feeds/top`
- `GET /feeds/new`
- `GET /feeds/jobs`
- `GET /posts/{post_id}`
- `GET /posts/{post_id}/comments`

Why second:

- read paths are lower-risk than writes
- they establish serializers, query patterns, and response-shape discipline
- they make it easier to validate the product loop before mutation endpoints expand

Scope notes:

- use the response shapes from `API_SPEC.md`
- keep cursor pagination and `page_info` envelope aligned with the spec
- ensure jobs stay separate from the main feed contract
- use persisted counters and scores from the `posts` table rather than recomputing them in read paths by default
- avoid N+1 query patterns through explicit query shaping and bounded eager loading

### Slice 3: Post and Comment Creation

Status: **implemented**

Implement after reads are stable:

- `POST /posts`
- `POST /posts/{post_id}/comments`

Required concerns:

- authenticated user resolution
- request validation by `post_type`
- comment parent validation through service logic on top of DB constraints
- slug generation
- domain/source linkage where needed
- counter updates and transactional integrity

Why third:

- creation flows rely on auth/session and shared serializers
- this is where service-boundary discipline starts to matter materially

### Slice 4: Voting

Status: **implemented**

Implemented last in the initial Phase 3 set:

- `POST /posts/{post_id}/vote`
- `DELETE /posts/{post_id}/vote`
- `POST /comments/{comment_id}/vote`
- `DELETE /comments/{comment_id}/vote`

Required concerns:

- authenticated user resolution
- one-vote-per-user-per-target enforcement
- vote replacement/removal semantics per API contract
- aggregate count updates
- synchronous aggregate/score updates for Phase 3 correctness
- ranking-trigger hooks where appropriate, without depending on Phase 6 worker infrastructure

Why fourth:

- voting is central, but it depends on posts/comments/auth already being stable
- it also has cross-cutting ranking implications, so it should land after the core read/write contracts are in place

---

## Implementation Strategy

For each slice:

1. implement routes, request/response schemas, service functions, and tests together
2. keep route handlers thin and push business rules into domain services
3. update docs/checklists if the implementation clarifies or changes a prior assumption
4. do not move to the next slice on broken tests in a previously working critical path

No slice should be treated as complete without tests for both happy-path and permission/security failure-path behavior.

---

## Testing Requirements

Minimum Phase 3 checkpoints from `DEVELOPMENT_TEST_CHECKPOINTS.md`:

- auth endpoint integration tests
- verification endpoint integration tests
- resend-verification endpoint integration tests
- verification delivery adapter tests
- session-cookie tests
- CSRF integration tests
- origin-validation tests
- post creation tests
- comment creation tests
- post vote and comment vote tests
- feed endpoint tests for `top`, `new`, and `jobs`
- permission tests for protected routes

Security-critical regressions to catch:

- missing `HttpOnly` / `Secure` / `SameSite` cookie settings
- mutating requests succeeding without CSRF
- unauthorized users reaching protected routes
- pending accounts receiving authenticated privileges before verification

Phase 3 exit criteria:

- the core loop works through API only
- the auth security contract holds
- feed routes return correct shapes and permissions

---

## Current Execution State

- Slice 1 is implemented and test-covered.
- Slice 2 is implemented and test-covered.
- Slice 3 is implemented and test-covered.
- Slice 4 is implemented and test-covered.
- Slice 1 is still pending live production email cutover, but that does not block Slice 2 implementation.
- Phase 3 core API scope is now implemented end to end.

This file should now be treated as the locked Phase 3 implementation plan unless a later doc review explicitly changes it.
