# PHASE3_CORE_API_PLAN.md

## Purpose

This file defines the execution plan for **Phase 3: Core API** after Phase 2 database and migration validation completed successfully.

This is a planning note, not an implementation log. The intended workflow for Phase 3 is:

1. plan
2. review each slice
3. implement only after agreement

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

These rules are locked unless explicitly reconsidered during review:

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

Implement first:

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`

Supporting work included in this slice:

- password hashing and verification
- session creation in `user_sessions`
- session invalidation
- current-session resolution dependency/helper
- secure cookie issuance
- CSRF token strategy for mutating requests
- origin-validation policy for browser-based state-changing requests

Why first:

- all protected write routes depend on it
- security mistakes here would leak into every later slice
- `SERVICE_BOUNDARIES.md` makes identity/session ownership explicit

Open decision to settle during auth review:

- final email canonicalization and uniqueness policy for auth flows

### Slice 2: Read-Only Core Loop Endpoints

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
- keep pagination format aligned with the spec
- ensure jobs stay separate from the main feed contract

### Slice 3: Post and Comment Creation

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

Implement last in the initial Phase 3 set:

- `POST /posts/{post_id}/vote`
- `POST /comments/{comment_id}/vote`

Required concerns:

- authenticated user resolution
- one-vote-per-user-per-target enforcement
- vote replacement/removal semantics per API contract
- aggregate count updates
- ranking-trigger hooks where appropriate

Why fourth:

- voting is central, but it depends on posts/comments/auth already being stable
- it also has cross-cutting ranking implications, so it should land after the core read/write contracts are in place

---

## Implementation Strategy

For each slice:

1. review the relevant spec section and current code layout
2. identify open decisions and service boundaries
3. agree on the contract and shape
4. implement routes, schemas, services, and tests together
5. update docs/checklists if the implementation clarifies or changes a prior assumption

No slice should be treated as complete without tests for both happy-path and permission/security failure-path behavior.

---

## Testing Requirements

Minimum Phase 3 checkpoints from `DEVELOPMENT_TEST_CHECKPOINTS.md`:

- auth endpoint integration tests
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

Phase 3 exit criteria:

- the core loop works through API only
- the auth security contract holds
- feed routes return correct shapes and permissions

---

## Immediate Next Review Target

Start with **Slice 1: Auth and Session Foundation**.

Before implementation, review:

- auth endpoint request/response shapes in `API_SPEC.md`
- session cookie contract
- CSRF/origin expectations
- identity-domain ownership from `SERVICE_BOUNDARIES.md`
- the unresolved email canonicalization decision captured during Phase 2 review

This review should produce the concrete implementation plan for the auth slice before any Phase 3 code is written.
