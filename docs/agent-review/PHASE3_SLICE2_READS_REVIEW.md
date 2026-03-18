# PHASE3_SLICE2_READS_REVIEW.md

## Purpose

This note locks the implementation direction for **Phase 3 Slice 2: Read-Only Core Loop Endpoints** before code starts.

Slice 1 auth/session work is complete enough to support viewer-aware reads, so the next job is to expose the core product loop through stable read endpoints.

Status: **implemented**

---

## Endpoints In Scope

Implement in this slice:

- `GET /feeds/top`
- `GET /feeds/new`
- `GET /feeds/jobs`
- `GET /posts/{post_id}`
- `GET /posts/{post_id}/comments`

Not in this slice:

- `GET /feeds/ask`
- `GET /feeds/show`
- `GET /posts/{post_id}/{slug}`
- any write endpoints

Those routes are valid future additions, but they are not required to land Slice 2.

---

## Locked Direction

### 1. Response contract stays aligned with `API_SPEC.md`

Feed responses use:

- `items`
- `page_info.next_cursor`
- `page_info.has_next_page`

Post detail response uses:

- `post`

Post comments response uses:

- `items`
- `page_info`

Do not improvise alternate envelopes.

### 2. Feeds only return active, publicly visible posts

For Slice 2, feeds should return only rows where:

- `posts.status = active`

This is the safe default public-read behavior.

Jobs feed also applies:

- `post_type = job`
- `job_expires_at IS NULL OR job_expires_at > now()`

### 3. Read paths should use persisted counters and scores

Feed and post detail reads should use stored fields on `posts`:

- `upvote_count`
- `downvote_count`
- `comment_count`
- `score`
- `rank_score`

Do not recalculate these from vote/comment tables in Slice 2.

### 4. Viewer-aware fields are supported, but only where cheap and explicit

These response fields should be filled:

- `viewer_vote`
- `viewer_can_edit`
- `viewer_can_moderate`

Rules:

- unauthenticated request: `viewer_vote = null`, permission flags `false`
- authenticated request:
  - feed lists and comment lists should use a second targeted vote query keyed by page ids plus viewer id
  - post detail may use an explicit join for the single requested row
- `viewer_can_edit` can be `true` only when:
  - the viewer is the author
  - and the resource status is `active`
- `viewer_can_moderate` can be `true` for moderator/admin roles

Do not overcomplicate author-edit-window policy in Slice 2 reads. A conservative `author == viewer` rule is acceptable until write policies are implemented.

### 5. Query count must stay bounded

Avoid N+1 reads.

Allowed approaches:

- explicit joins
- bounded eager loading
- a second targeted query for viewer votes if it stays bounded per page

The goal is disciplined query shaping, not "one giant query at all costs."

### 6. Cursor pagination should be stable and opaque

For feeds:

- `top` should paginate on `rank_score desc, id desc`
- `new` should paginate on `submitted_at desc` plus `id` as a tiebreaker
- `jobs` should paginate on its chosen public ordering plus `id` as a tiebreaker

Cursor contents should be opaque to clients.

Implementation detail can be simple v1 base64/json as long as:

- ordering is deterministic
- ties do not duplicate/drop rows across pages

Important nuance for `top`:

- the cursor should encode both `rank_score` and `id`
- `top` pagination is **best-effort consistent**, not perfectly stable across later score refreshes

### 7. Comments stay flat in the API response

`GET /posts/{post_id}/comments` should return a flat list including:

- `parent_comment_id`
- `depth`

The client is still responsible for tree reconstruction.

### 8. Comment sorting

Support the spec's comment `sort` values:

- `top`
- `new`
- `old`

Recommended ordering:

- `top`: `rank_score desc`, `id desc` tiebreaker
- `new`: `created_at desc`, `id desc`
- `old`: `created_at asc`, `id asc`

Comments are **not paginated in Slice 2**.

Reason:

- the current spec only defines `sort`, not comment `limit/cursor`
- paginating a flat thread response complicates client-side reconstruction immediately
- a full flat list is the simpler MVP contract

If `page_info` remains in the response for envelope consistency, it should be:

- `next_cursor = null`
- `has_next_page = false`

### 9. Post detail route is by ID only for this slice

Implement:

- `GET /posts/{post_id}`

Do not add slug-routing behavior in Slice 2 unless it becomes necessary for frontend integration immediately.

### 10. Route handlers stay thin

Expected ownership split:

- API layer: request parsing, dependency wiring, response models
- backend/domain layer: feed queries, post lookup, comment lookup, cursor logic, viewer-awareness shaping

Do not put ORM-heavy query logic directly in FastAPI route handlers.

---

## Data Needed Per Resource

### Feed item / post detail

Each returned post needs:

- core post fields from `posts`
- author identity (`id`, `username`)
- optional domain summary (`id`, `hostname`, `display_name`)
- optional viewer post vote

No ingestion payloads, raw source metadata, or moderation internals belong in public Slice 2 responses.

### Comment item

Each returned comment needs:

- core comment fields from `comments`
- author identity (`id`, `username`)
- viewer comment vote

Replies are not nested server-side in this slice.

---

## Implementation Notes

### Feed ordering

- `top`: `status = active`, ordered by `rank_score desc, id desc`
- `new`: `status = active`, ordered by `submitted_at desc, id desc`
- `jobs`: `status = active`, `post_type = job`, not expired, ordered by `submitted_at desc, id desc`

### Missing-resource behavior

- missing post: `404 post_not_found`
- comments for missing post: also `404 post_not_found`
- non-active post requested through public read routes: also `404 post_not_found`

### Auth on read routes

Read routes remain publicly accessible.

If a valid session cookie is present, enrich the response with viewer-aware fields.
If not, return the public shape.

---

## Test Expectations

Minimum tests for this slice:

- `GET /feeds/top` returns correct envelope and ordering
- `GET /feeds/new` returns correct envelope and ordering
- `GET /feeds/jobs` includes null-expiry jobs
- `GET /feeds/jobs` includes future-expiry jobs
- `GET /feeds/jobs` excludes expired jobs
- feed pagination returns stable `page_info`
- unauthenticated feed responses show `viewer_vote = null`
- authenticated feed responses surface viewer vote where present
- `GET /posts/{post_id}` returns the full post shape
- missing post returns `404 post_not_found`
- non-active post returns `404 post_not_found`
- `GET /posts/{post_id}/comments?sort=top`
- `GET /posts/{post_id}/comments?sort=new`
- `GET /posts/{post_id}/comments?sort=old`
- comments route returns flat comments with parent/depth fields

---

## Immediate Next Build Order

1. API response schemas for feed items, post detail, comments, and `page_info`
2. backend read/query service layer for posts and comments
3. cursor helpers for feed pagination
4. feed routes
5. post detail route
6. post comments route
7. focused Slice 2 tests
