# Phase 3 Read Layer Hardening Review

Date: `2026-03-18`
Status: `implemented`

## Agreed Fixes

- Strengthen malformed feed-cursor handling so missing or bad cursor fields return `400 validation_error` instead of surfacing raw `500` failures.
- Remove `url_normalized` and `is_ingested` from the public `PostPayload` shape. They are internal normalization/provenance details, not required public read fields.
- Add a temporary safety cap of `500` comments in `get_post_comments()` until real comment pagination is designed.
- Tighten `_viewer_context()` typing in feed and post routes to `UUID | None` and `UserRole | None`.
- Add targeted read-helper tests for malformed cursor payloads beyond simple bad base64.

## Explicit Non-Fixes

- `_viewer_can_edit()` is not currently broken. The mixed `PostStatus.ACTIVE` / `CommentStatus.ACTIVE` membership check works because these enums are `StrEnum`s with equal values.
- No immediate route-layer validation refactor for read responses. The current priority is read-path hardening, not broad boundary reshaping.
- No change to job creation rules around past `job_expires_at` in this pass.
- No comment-pagination contract added in this pass. The temporary cap is only a safety ceiling.
- No change yet to removed-parent reply UX in flat comment responses.

## Implemented Result

- Malformed or incomplete feed cursors now fail cleanly with the existing `validation_error` envelope.
- Public post responses no longer expose `url_normalized` or `is_ingested`.
- Post comments are currently capped at `500` rows per request as a temporary guardrail.
- Route helper typing is now concrete instead of `object`-based.
