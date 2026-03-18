# PHASE3_API_HARDENING_REVIEW.md

## Purpose

This note captures the post-Phase-3 hardening pass driven by manual API testing feedback.

The goal is not to redesign the API. The goal is to tighten the existing implementation and validation surfaces where the public auth and mutation routes still have avoidable gaps.

---

## Locked Non-Changes

These points were discussed and are explicitly **not** being changed in this hardening pass:

- local development and production cookie expectations remain different
  - local HTTP dev should continue to work without `Secure=True`
  - production/staging HTTPS should still require secure cookies
- the shared write guard stays a backend/service-layer helper
  - it does **not** move to a FastAPI `Depends()` guard

---

## Agreed Hardening Work

### 1. Verification token edge-case coverage

Add explicit validation for:

- expired verification token
- already-consumed / already-used verification token
- malformed / garbage verification token

This is primarily a testing and manual-validation gap. The current implementation already has branches for these states.

### 2. Logout invalidation coverage

Add validation that:

- logout clears the cookie client-side
- the old session token is also invalid server-side

This is important to prove we are not only doing client-side cookie clearing.

### 3. Auth rate-limit coverage

Add coverage for:

- in-memory limiter behavior itself
- route behavior when the limiter blocks the request

The limiter already exists, but it was under-tested.

### 4. Login timing hardening

Current message-level enumeration is already controlled:

- unknown email -> `401 invalid_credentials`
- wrong password -> `401 invalid_credentials`

The remaining improvement is timing parity:

- unknown-user login should still do a dummy password verification pass

This is a real code hardening change.

### 5. Manual guide coverage expansion

Update the Phase 3 API test guide to include:

- used / expired / garbage verification-token checks
- resend-verification checks
- old-session-after-logout check
- unauthenticated viewer-field assertions
- cursor-following pagination check
- `sort=new` and `sort=old` comment checks
- cross-post parent comment injection check
- expired job filtering check
- missing-target vote check
- shell-variable reminders for `POST_ID` and `COMMENT_ID`
- current self-vote behavior note
- cookie-name/config note for CSRF extraction
- local-vs-production cookie flag expectations

### 6. Code review checklist expansion

Add explicit review prompts for:

- unicode slug behavior
- shared write-guard behavior
- resend-verification flow

---

## Expected Deliverables

This hardening pass should produce:

1. a timing-parity improvement in auth login handling
2. new automated tests for the agreed auth/security gaps
3. an updated Phase 3 API manual guide
4. no change to the write-guard architecture
5. no change to the dev-vs-prod cookie split

---

## Success Criteria

The hardening pass is complete when:

- the focused suite still passes
- the new auth/security edge cases are covered by tests
- the manual guide reflects the actual security-critical behaviors we want reviewers to validate
