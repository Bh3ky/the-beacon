# PHASE3_AUTH_SLICE_REVIEW.md

## Purpose

This note captures the reviewed decisions for **Phase 3 Slice 1: Auth and Session Foundation** before implementation starts.

It exists because the original Phase 3 plan assumed a relatively lean auth slice, but review feedback expanded the scope into a verification-first auth model.

---

## Locked Decisions

### 1. Session model

Use **database-backed opaque sessions**.

Rules:

- the browser holds a random opaque session token
- the database stores only `session_token_hash`
- the raw token is never persisted server-side
- logout invalidates the session by deleting or otherwise invalidating the session row
- future "log out all devices" remains possible by deleting all session rows for the user

This is already aligned with the current `user_sessions` model shape.

### 2. Registration model

Use **verification-first registration**.

Rules:

- `POST /auth/register` creates an account in a pending, non-authenticated state
- registration does **not** issue a logged-in session
- registration does **not** set the authenticated session cookie
- verification completion is what authenticates the user

Implication:

- the current schema and API contract are not sufficient as-is
- this requires a small schema and spec expansion before auth implementation

### 3. Verification completion behavior

After successful verification:

- create authenticated session
- set auth cookie
- set CSRF cookie
- return the authenticated-user response shape used by login

### 4. Logout behavior

`POST /auth/logout` is **idempotent**.

Rules:

- attempt current-session invalidation if session exists
- clear auth cookie
- clear/invalidate CSRF cookie
- return `204 No Content` regardless of whether a valid session was present

### 5. Session lifetime policy

Use **fixed max lifetime plus sliding idle timeout**.

Recommended initial values from review:

- idle timeout: `30 minutes`
- absolute lifetime: `24 hours`

Field roles:

- `created_at` = absolute-lifetime anchor
- `last_seen_at` = activity marker
- `expires_at` = current effective expiry, extended on qualified activity but capped by absolute lifetime

### 6. Session touch throttling

Do not update session activity on every request.

Rule:

- if `now - last_seen_at >= 10 minutes`, update `last_seen_at`
- at the same time, extend `expires_at` within the absolute-lifetime cap

### 7. Email canonicalization

Canonicalize emails in the auth service layer before both write and lookup.

Locked policy:

- trim surrounding whitespace
- lowercase the full address
- do not strip dots
- do not strip plus aliases

Reason:

- avoids duplicate-account bugs from case drift
- avoids incorrect provider-specific alias collapsing

### 8. CSRF model

Use a **session-bound signed double-submit** pattern.

Rules:

- auth session cookie is `HttpOnly`
- CSRF cookie is readable by browser JavaScript
- mutating requests must send CSRF token via header
- server validates:
  - CSRF header present
  - CSRF cookie present
  - header token equals cookie token
  - token is cryptographically tied to the authenticated session or validated against server-held session state

Supporting rule:

- add `Origin` validation for state-changing requests as a second layer

Cookie lifecycle:

- `POST /auth/login` sets auth cookie + CSRF cookie
- `POST /auth/verify` sets auth cookie + CSRF cookie
- `GET /auth/me` refreshes CSRF cookie if authenticated and missing
- `POST /auth/logout` clears auth and CSRF cookies

### 9. Rate limiting

Add minimal Phase 3 auth rate limiting.

Initial reviewed targets:

- register: `3/hour/IP`, optionally `5/day/IP`
- login: `5/minute/IP`
- login: additional `10/15 minutes` by account/email key
- logout: no meaningful limit initially

This is intended as Phase 3 abuse protection, not the final distributed production design.

---

## Required Spec And Schema Follow-Ups

Path B cannot be implemented cleanly without first acknowledging these gaps:

### API contract gap

Current `API_SPEC.md` defines:

- `POST /auth/register`
- `POST /auth/verify`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`

### Schema gap

Current user/session schema must support:

- a pending verification user lifecycle state in `user_status_enum`
- dedicated verification token storage instead of overloading `user_sessions`

That makes Slice 1 a Phase-3-level schema/spec adjustment, not just route work.

---

## Recommended Next Review Questions

Before coding, keep these implementation details explicit:

1. `POST /auth/register` returns a pending user shape plus `verification_required = true`.

2. `POST /auth/verify` accepts an opaque verification token and returns the same authenticated-user shape as login.

3. Login rejects unverified accounts with `403 account_pending_verification`.

---

## Implementation Boundary Reminder

This remains an auth/identity slice, not a reason to let business logic leak into route handlers.

Expected ownership:

- identity domain owns registration, verification, login/logout, session creation, session invalidation, CSRF helpers, and current-session resolution
- route handlers stay thin
- user profile/public serialization remains separate from auth/session internals
