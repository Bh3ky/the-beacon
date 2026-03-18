# Phase 3 Model, Schema, and Coverage Review

Date: `2026-03-18`
Status: `implemented`

## Agreed Fixes

- Enforce the locked "one active verification token per user" rule at the database level instead of relying only on service-layer delete-and-insert sequencing.
- Add explicit metadata coverage for the new active verification-token partial unique index.
- Add a real service-level test for duplicate-link integrity translation in `create_post()`, not only helper-level constraint-name detection.

## Rationale

- `user_verification_tokens` previously guaranteed token uniqueness only by `token_hash`, not by active token ownership per user.
- The duplicate-link race handling for `create_post()` was implemented, but the suite only tested the small integrity-classification helper instead of the actual service behavior.

## Implemented Result

- Active verification tokens are now guarded by a PostgreSQL partial unique index on `user_id` where `consumed_at IS NULL`.
- Resend-verification now locks the pending user row before rotating tokens so concurrent resend requests serialize cleanly.
- The creation-layer suite now exercises the real `IntegrityError -> 409 duplicate_submission` translation path.
