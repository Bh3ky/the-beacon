# Phase 3 Creation Layer Hardening Review

Date: `2026-03-18`
Status: `implemented`

## Agreed Fixes

- Strip URL fragments during normalization so link dedupe does not treat `#fragment` variants as distinct submissions.
- Add a database-backed duplicate-link race guard for active link posts using a partial unique index on `posts.url_normalized`.
- Catch duplicate-link integrity errors in the creation service and re-raise them as the existing `409 duplicate_submission` API contract.
- Add explicit comments documenting that ASCII-only slug generation is an intentional v1 compromise and that transliteration is a future improvement.
- Clarify that `MAX_COMMENT_DEPTH = 6` means root depth `0` plus replies up to depth `6`.

## Explicit Non-Fixes

- No trailing-slash normalization in this pass. That is a product-level equivalence decision, not a safe one-line cleanup.
- No query-parameter order normalization in this pass.
- No change to route-boundary validation in `CreatePostRequest` yet; the service layer remains the main owner of business validation.
- No change to job duplicate detection policy yet; duplicate URL handling remains specific to link posts.
- No change yet to `last_commented_at` time source.

## Implemented Result

- Normalized URLs now drop fragments before storage and comparison.
- Concurrent active link submissions now have a DB-level uniqueness guard instead of relying only on a pre-insert `SELECT`.
- Duplicate-link integrity failures are converted into the same `409 duplicate_submission` envelope as the pre-check path.
