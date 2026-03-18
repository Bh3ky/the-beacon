# PHASE3_SLICE3_CREATION_REVIEW.md

## Purpose

This note locks the implementation direction for **Phase 3 Slice 3: Post and Comment Creation** before code starts.

Slice 2 read routes are now in place, so the next step is to make the core loop writable through authenticated post and comment creation endpoints.

Status: **implemented**

---

## Endpoints In Scope

Implement in this slice:

- `POST /posts`
- `POST /posts/{post_id}/comments`

Not in this slice:

- post edit/update
- post remove/delete
- comment edit/update
- comment remove/delete
- bookmark flows
- moderation write flows

Those routes belong to later slices or later Phase 3 extensions.

---

## Locked Direction

### 1. Auth is required for both endpoints

Both creation routes require an authenticated session.

Because Slice 1 already locked session-bound CSRF and origin validation, Slice 3 should consume those protections rather than re-invent them.

### 2. Route handlers stay thin

Expected ownership:

- API layer:
  - request parsing
  - dependency wiring
  - response serialization
  - CSRF enforcement
- backend/domain layer:
  - post/comment validation
  - slug generation
  - URL normalization
  - domain linkage
  - duplicate detection
  - comment depth/parent checks
  - transactional writes

### 3. `POST /posts` must validate by `post_type`

The current schema already enforces broad structural constraints, but the service layer must fail early with API-friendly errors.

Rules:

- `title` is always required
- `category` is always required
- `post_type` is always required
- `link` posts require `url`
- `text` posts require `body_markdown`
- `job` posts require at least one of:
  - `url`
  - `body_markdown`

### 4. New posts are user-created active rows

For Slice 3 user submissions:

- `status = active`
- `is_ingested = false`
- aggregate counters initialize from stored defaults
- `submitted_at` comes from the application write path

No special moderation holding state is introduced in this slice.

This is a deliberate v1 product decision:

- verified users are trusted to publish directly to active state
- moderation queue behavior is a future slice concern, not part of Slice 3

### 5. Slug generation must be deterministic

We do not yet have a slug helper in code, so Slice 3 must introduce one.

Locked requirements:

- lowercase
- URL-safe
- based on title
- stable for the submitted title
- deterministic/pure
- maximum slug length: `100`

Important current constraint:

- `slug` is intentionally **not globally unique**
- route resolution still relies on `id`, not slug-only lookup

So Slice 3 does **not** need slug uniqueness enforcement beyond generating a reasonable slug string.

Degenerate-slug fallback:

- if normalization produces an empty slug, fall back to `post`

### 6. URL normalization must be explicit

We do not currently have a shared URL-normalization helper.

Slice 3 must add one for post creation.

Minimum v1 normalization policy:

- trim surrounding whitespace
- require `http` or `https`
- lowercase scheme and host
- remove default port if present
- preserve path semantics

Do not overreach into aggressive canonicalization without a locked policy.

### 7. Duplicate submission behavior should stay conservative

The broader `posts.url_normalized` dedupe policy is still an open product follow-up, so Slice 3 should implement only the minimum contract already described in `API_SPEC.md`.

Recommended v1 behavior:

- for `link` posts, check for an existing active post with the same `url_normalized`
- if found, return:
  - `409 duplicate_submission`
  - include `existing_post_id`
  - include `existing_post_slug`

This is a practical v1 duplicate rule, not a final repost-window system.

The duplicate check must always use the normalized URL, not the raw submitted URL.

### 8. Domain linkage happens during link/job creation

For post types that carry a URL:

- derive the hostname from the normalized URL
- look up an existing `domains` row
- create one if absent
- set `domain_id`

The resolution pattern must be DB-safe under concurrency:

- do not use naive check-then-insert
- use an upsert-safe pattern such as insert-on-conflict followed by fetch

For text posts:

- `url = null`
- `url_normalized = null`
- `domain_id = null`

### 9. `job_expires_at` remains permissive

Do not tighten job expiry semantics in Slice 3 beyond existing schema rules.

Allowed:

- `job` post with `job_expires_at = null`
- `job` post with future expiry

Do not force expiry on job posts in this slice.

### 10. Comment creation must respect same-post parentage and depth

Rules:

- `body_markdown` is required
- top-level comment:
  - `parent_comment_id = null`
  - `depth = 0`
- reply:
  - parent comment must exist
  - parent comment must belong to the same post
  - new depth = `parent.depth + 1`

Even though the DB now enforces same-post parentage, the service should still produce clean API-level validation errors before constraint failures leak through.

### 11. Max comment depth needs a v1 number

The spec says max depth is policy-defined, but the value is not yet explicit in code.

Recommended Slice 3 default:

- maximum depth = `6`

That is deep enough for real threads without encouraging unreadable nesting.

### 12. Post/comment creation should update simple aggregates synchronously

Slice 3 should keep correctness local and synchronous.

At minimum:

- post creation requires no extra aggregate work beyond defaults
- comment creation should update the parent post:
  - `comment_count += 1`
  - `last_commented_at = now`

Do not defer those two comment-side updates to a future worker.

### 13. Response shape should reuse Slice 2 serializers

Creation responses should return the same resource shape already used in Slice 2:

- `POST /posts` returns `{ "post": ... }`
- `POST /posts/{post_id}/comments` returns `{ "comment": ... }`

This keeps read/write payloads aligned and avoids parallel serializer drift.

---

## Error Behavior

### Post creation

Expected failures:

- `401 unauthenticated`
- `403 forbidden` only for authenticated users whose account state is `suspended` or `banned`
- `404` only if a supporting linked resource lookup somehow becomes explicit later
- `409 duplicate_submission` for normalized duplicate link posts
- `422 validation_error` for bad request payloads

### Comment creation

Expected failures:

- `401 unauthenticated`
- `403 forbidden` only for authenticated users whose account state is `suspended` or `banned`
- `404 post_not_found`
- `404 comment_not_found` for bad parent id
- `422 validation_error` for invalid body or depth overflow

For this slice, pending users should never reach these endpoints because auth/session issuance already requires verification.

---

## Implementation Notes

### Post service responsibilities

The post-creation service should:

1. validate payload by `post_type`
2. generate slug
3. normalize URL if present
4. resolve/create domain if URL present
5. check duplicate active normalized URL for link posts
6. insert post with explicit `submitted_at`
7. return the same post-read shape used by Slice 2, including resolved domain summary where applicable

### Comment service responsibilities

The comment-creation service should:

1. verify target post exists and is active
2. validate body
3. resolve parent if provided
4. compute depth
5. reject depth overflow
6. insert comment
7. update post aggregate fields using SQL-side atomic update patterns
8. return the same comment-read shape used by Slice 2

---

## Immediate Missing Helpers

Slice 3 will need new backend helpers for:

- slug generation
- URL normalization
- hostname extraction/domain resolution

These do not exist yet and should be added deliberately rather than improvised inline in route handlers.

---

## Test Expectations

Minimum tests for this slice:

- authenticated `POST /posts` creates a text post
- authenticated `POST /posts` creates a link post and links/creates domain
- authenticated `POST /posts` creates a job post
- authenticated `POST /posts` creates a job post with body only and no URL
- link post duplicate returns `409 duplicate_submission`
- invalid `post_type` payload returns `422`
- suspended or banned authenticated user receives `403` on post creation
- unauthenticated `POST /posts` returns `401`
- authenticated `POST /posts/{post_id}/comments` creates a top-level comment
- authenticated `POST /posts/{post_id}/comments` creates a reply with computed depth
- comment parent from another post is rejected cleanly
- comment creation beyond max depth is rejected
- suspended or banned authenticated user receives `403` on comment creation
- unauthenticated `POST /posts/{post_id}/comments` returns `401`
- comment creation updates `comment_count` and `last_commented_at`

---

## Recommended Build Order

1. request/response schemas for post/comment creation
2. slug helper
3. URL normalization + hostname/domain resolution helper functions
4. backend post-creation service
5. backend comment-creation service
6. API routes with CSRF enforcement
7. focused Slice 3 tests
