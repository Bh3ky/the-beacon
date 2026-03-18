# PHASE3_EMAIL_VERIFICATION_DELIVERY_REVIEW.md

## Purpose

This note locks the delivery-channel decisions for Phase 3 email verification after Slice 1 auth foundation work.

It exists because the auth slice already creates verification tokens and stores only their hashes, but delivery is still a development-only logging path. That is sufficient for local testing, but not operationally complete.

---

## Current State

Implemented already:

- pending-user registration
- verification token generation
- token-hash storage
- verification endpoint
- session issuance after verification

Current limitation:

- verification tokens are still surfaced through development logging rather than a real delivery transport

---

## Locked Decisions

### 1. Delivery stays behind a port

Auth owns:

- user creation
- token creation
- token-hash persistence
- token expiry/consumption rules
- verification

Delivery owns:

- sending the prepared verification message
- provider-specific formatting and transport

Auth must not depend directly on a provider SDK.

### 2. Verification URL is built outside the delivery adapter

The auth/application layer should build the verification URL from config and pass it into the delivery adapter.

Reason:

- the delivery adapter should not own frontend routing knowledge
- changing the frontend verification route should not require changing provider adapters

### 3. Verification link lifetime

Use a default verification token TTL of **24 hours**.

Reason:

- verification is lower-risk than password reset
- this is long enough for normal email-delivery delays
- this is short enough to keep old links from lingering indefinitely

### 4. Token validity policy

Verification tokens are:

- opaque
- single use
- stored only as hashes
- rejected after expiry

Only **one active verification token per user** should exist at a time.

If a new verification token is issued for the same user, prior unconsumed tokens should be invalidated or deleted.

### 5. Delivery payload shape

The delivery port should accept a prepared payload, not raw auth internals.

Minimum payload:

- recipient email
- username or display name
- verification URL
- expiry timestamp

The delivery port should not:

- create tokens
- read auth tables directly
- determine token expiry rules

### 6. Environment strategy

Use environment-specific delivery adapters:

| Environment | Adapter |
| --- | --- |
| local development | Mailpit preferred, logging fallback |
| CI/tests | no-op adapter |
| staging | Resend adapter after domain verification |
| production | Resend adapter after domain verification |

### 7. Logging policy

Raw verification tokens or full verification URLs may be logged only in **local development**.

They must not be logged in:

- staging
- production

### 7.1 First production provider

The first real provider adapter should be **Resend**.

Current implementation direction:

- keep `mailpit` or `log` for local development
- keep `noop` for tests
- ship a dormant `resend` adapter behind configuration
- do not enable `resend` until:
  - a real sending domain has been purchased
  - the domain has been verified in Resend
  - a `RIFTHUB_RESEND_API_KEY` secret exists
  - `RIFTHUB_VERIFICATION_FROM_EMAIL` uses the verified domain

Reason:

- this lets Phase 3 progress without blocking on domain purchase
- it also makes the production cut-over a config change instead of a refactor

### 8. Verification base URL source

Verification links must use an explicit configured frontend/app base URL.

Do not derive verification hosts from request headers.

Reason:

- prevents host-header confusion
- keeps email links stable across API deployments

### 9. Delivery failure semantics

Delivery failure must not be treated as transactionally atomic with database commit.

We cannot make:

- pending user creation
- token persistence
- external email delivery

one atomic operation.

So the system should treat delivery as:

- token committed in DB
- delivery attempted after the relevant DB state is durable
- failures logged and surfaced through retry/resend flow rather than crashing mid-transaction

### 10. Resend behavior

Phase 3 should include a dedicated resend path rather than relying on repeated registration attempts.

Recommended contract direction:

- add `POST /auth/resend-verification`
- rotate the active verification token
- invalidate prior unconsumed token(s)
- trigger delivery again

This should be treated as part of operational auth completeness, not a later polish item.

---

## Recommended URL Shape

Default v1 verification URL:

```text
https://app.example.com/verify?token=<opaque-token>
```

This is acceptable for v1.

Optional later hardening:

- fragment-based token transport, such as `#token=...`, if frontend flow and logging posture justify it

---

## Implementation Consequences

The current auth service should be revised so that:

1. registration creates and persists the token
2. the service builds the verification URL from configured base URL
3. the service calls a delivery port with a prepared payload
4. only local-dev adapters may expose the raw token or URL in logs

The current "debug-log the token" behavior should be treated as a temporary local-development adapter, not as the long-term service behavior.

---

## Follow-Up Docs To Sync

If we adopt the resend path in implementation, the following docs must be updated before or alongside code:

- `docs/API_SPEC.md`
- `docs/ROADMAP.md`
- `docs/SECURITY.md`
- `docs/agent-review/PHASE3_CORE_API_PLAN.md`

---

## Implementation Order

1. Add delivery configuration and frontend verification base URL
2. Define the delivery port and payload shape
3. Move current log-based behavior into a dev-only adapter
4. Add no-op test adapter
5. Add Mailpit adapter for local development
6. Add resend-verification contract and route
7. Add real provider adapter later
