# Feedback on Read Layer

1. `reads.py`

- `_viewer_can_edit` mixes PostStatus and `CommentStatus` in a single set comparison - this will silently fail

```python
def _viewer_can_edit(*, viewer_user_id, author_id, status: PostStatus | CommentStatus) -> bool:
    return viewer_user_id == author_id and status in {PostStatus.ACTIVE, CommentStatus.ACTIVE}
```

- if `PostStatus` and `CommentStatus` are separate Python enums, `PostStatus.ACTIVE` and `CommentStatus.ACTIVE` are different objects even if they have the same string value. A `PostStatus.ACTIVE` check against a set containing `CommentStatus.ACTIVE` will return `False`. This means `viewer_can_edit` will always be `False` for posts or always for comments depending on which enum variant is in the set. Verify this in a Python shell with your actual enum definitions — if they’re separate enums, split this into two functions or compare .value directly.

- decode_feed_cursor catches all exceptions with a bare except Exception but the pragma: no cover comment suggests this path is never tested.

```python
except Exception as exc:  # pragma: no cover - defensive parse guard
```

- The base64 decode and JSON parse can realistically fail on malformed client input — this isn’t a hypothetical path. A user sending a corrupted or manually constructed cursor string should hit this branch. Remove the pragma: no cover and add a test for a malformed cursor (non-base64 string, valid base64 but invalid JSON). The defensive guard is correct; the coverage skip is not.

- apply_feed_cursor for the top feed uses float equality comparison on rank_score.

```python
apply_feed_cursor for the top feed uses float equality comparison on rank_score.
```

- Float equality in SQL is unreliable when rank_score is stored as a FLOAT or DOUBLE PRECISION. Two rows that should have the same rank score may differ by a floating-point epsilon depending on how PostgreSQL stores and retrieves the value. This means the tie-breaking id branch may never trigger for rows with nominally equal scores, causing rows to be silently dropped or duplicated across pages. The safer approach is to cast rank_score to NUMERIC for the equality comparison, or store rank_score as NUMERIC in the schema.

- get_post_comments has no pagination — this is a silent scalability bomb.

- There’s no limit applied. A post with 500 comments returns all 500 in a single response. The CommentPage always returns has_next_page=False and next_cursor=None, which confirms this is intentional for now — but the function signature has no limit or cursor parameter, meaning adding pagination later requires a breaking API change. At minimum, add a hardcoded safety cap (query.limit(500) or similar) so a single pathological post can’t bring down the response time, and note pagination as a follow-up.

- viewer_comment_votes uses IN query with an unbounded list.

```python
CommentVote.comment_id.in_(comment_ids),
```
- If get_post_comments returns all comments for a large post, comment_ids could be hundreds of UUIDs. Most databases handle large IN lists fine up to a few thousand, but PostgreSQL query planning degrades beyond ~1000 items and the query isn’t bounded anywhere. This is tied to the pagination gap above — fixing that fixes this.

- get_post_detail treats a removed/non-active post the same as a missing post.
_base_post_query() filters Post.status == PostStatus.ACTIVE, so a post that exists but is removed/hidden returns 404 post_not_found. This was discussed in the Slice 2 review and the decision was to use 404 to avoid leaking moderation state — that’s correct. But the current error message is "The requested post does not exist." which is technically false for a removed post. A more neutral message like "Post not found." covers both cases without lying.
-  _feed_page_info receives posts: list[Post] but is called after posts = posts[:limit] — correct, but fragile.
The slicing happens in _get_feed before calling _feed_page_info. If someone refactors the call order and passes the unsliced list, the cursor will encode the wrong last item. The function should either receive the already-sliced list with a clear parameter name (page_posts) or derive the last item internally. As written, the caller must remember to slice before calling.
- The jobs feed uses _apply_feed_cursor with kind="jobs", but the cursor payload is keyed on submitted_at — the same as new.
This works correctly because _apply_feed_cursor falls through to the submitted_at branch for any non-top kind, which includes jobs. But the kind field stored in the cursor is "jobs", and decode_feed_cursor validates that the cursor kind matches the feed kind. This means a new feed cursor cannot be accidentally used on the jobs feed, which is the right behaviour. The logic is correct but it’s non-obvious — worth a short comment explaining that jobs reuses the submitted_at cursor path intentionally.

Minor Points
_utcnow() is defined at module level but only used in _get_feed for the jobs expiry check. Fine as a utility, but since it’s not exported or used elsewhere, it’s slightly over-engineered. datetime.now(UTC) inline is equally readable for a single call site.
encode_feed_cursor uses sort_keys=True which is good — deterministic serialization prevents two logically identical cursors from encoding differently. Worth a comment explaining why, since sort_keys is not the default and a reviewer might remove it thinking it’s unnecessary.
PostRead exposes url_normalized in the response. This is the canonicalized form used internally for deduplication — consider whether you want clients to see it, or whether it should be omitted from the public read shape. For a public community platform this is probably fine, but it’s worth a deliberate decision.


2. feeds.py

Correctness Issues
1. _viewer_context return type annotation uses object | None instead of the actual types.

```python
def _viewer_context(current_session: CurrentSessionDep) -> tuple[object | None, object | None]:
```

This loses type information at the call site. viewer_user_id and viewer_role are passed directly into get_top_feed and siblings, which expect UUID | None and UserRole | None respectively. With object | None the type checker can’t catch a mismatch if those signatures ever change. Replace with the concrete types:

```python
from uuid import UUID
from rifthub_backend.db.types import UserRole

def _viewer_context(current_session: CurrentSessionDep) -> tuple[UUID | None, UserRole | None]:
```

Design Issues
2. _viewer_context is a module-level helper that does something a Depends() could do more explicitly.
The three feed routes all call _viewer_context(current_session) identically. This pattern works but it means the viewer context extraction is invisible to FastAPI’s dependency graph — it won’t show up in the OpenAPI schema or be injectable/mockable in tests without going through the full session dependency.
For three routes sharing identical context extraction, a small Depends() would make this more composable as the route count grows. Not a blocking issue for this slice, but worth noting as a refactor candidate before the posts and comments routes multiply the same pattern.
3. The three route handlers are structurally identical except for the service call.
top_feed, new_feed, and jobs_feed share the same signature, the same _viewer_context call, and the same FeedResponse.model_validate(...) wrapper. If the feed signature ever changes (adding a filter param, changing the default limit) you have three places to update. A private _feed_response helper that takes the coroutine result and wraps it would reduce that surface — though at this scale it’s a style preference, not a bug risk.

Minor Points
cursor: str | None = None has no length validation. A client can send an arbitrarily long cursor string. reads.py will fail to decode it gracefully, but the raw string is still parsed by FastAPI and passed into the decode function before any length check happens. A Query(default=None, max_length=512) guard would reject malformed cursors at the boundary rather than inside the service layer.
The tags=["feeds"] grouping is correct and will produce clean OpenAPI docs. No issues there.


3. `posts.py`

1. Same _viewer_context type annotation problem carried over from feeds.py.
Same tuple[object | None, object | None] return type. Fix it here too — same reasoning as the feeds review.
2. CreatePostRequest has no field-level validation on title, url, or body_markdown.
A client can submit an empty string title (""), a whitespace-only title ("   "), or a body_markdown of arbitrary length. If the service layer doesn’t enforce these either, empty posts can reach the database. At minimum:

```python
from pydantic import field_validator

title: str = Field(min_length=1, max_length=300)
body_markdown: str | None = Field(default=None, max_length=40000)
```

The url field also has no length cap or format hint — Pydantic’s AnyHttpUrl or a simple max_length would reject obviously malformed URLs before they reach the normalization helper.
3. job_expires_at accepts any datetime including values in the past.
A client can submit a job post with job_expires_at set to yesterday, which would create a job post that’s immediately invisible in the jobs feed. The route layer should reject past expiry dates:

```python
from pydantic import field_validator
from datetime import UTC, datetime

@field_validator("job_expires_at")
@classmethod
def expiry_must_be_future(cls, v):
    if v is not None and v <= datetime.now(UTC):
        raise ValueError("job_expires_at must be in the future")
    return v
```


Design Issues

4. CSRF validation is called manually in every mutation handler rather than as a dependency.
All five mutation routes (create_post_route, create_post_comment, create_post_vote, delete_post_vote, and implicitly any future mutations) call validate_session_csrf(request=request, settings=settings, current_session=current_session) as the first line. This is a copy-paste security gate — if someone adds a new mutation route and forgets the call, there’s no enforcement. A Depends() guard would make CSRF a structural requirement rather than a convention:

```python
def require_csrf(
    request: Request,
    settings: AppSettings,
    current_session: RequiredCurrentSession,
) -> None:
    validate_session_csrf(request=request, settings=settings, current_session=current_session)

CsrfProtected = Annotated[None, Depends(require_csrf)]
```

Then each mutation handler just declares _: CsrfProtected in its signature and the enforcement is automatic. This would also eliminate the need to inject Request and AppSettings individually into every mutation handler.

5. _viewer_context is duplicated from feeds.py.
Two identical private helpers in two files. This should live in dependencies.py as a shared utility or Depends() — same suggestion as the feeds review, more pressing now that it’s duplicated.

Minor Points
CreateCommentRequest.body_markdown has no length validation. Same issue as post body — a client can submit a 10MB comment body. Add Field(min_length=1, max_length=10000) or whatever your content policy is.
VoteRequest is defined in posts.py but comments.py likely defines an identical one. If so, this belongs in schemas.py as a shared request model. Worth checking when you post comments.py.
sort in post_comments duplicates the Literal["top", "new", "old"] type inline rather than reusing CommentSort from reads.py. These should stay in sync — if a sort option is added to reads.py it won’t automatically be accepted here. Import and reuse CommentSort directly.
Route ordering: GET /{post_id} is registered before GET /{post_id}/comments. FastAPI resolves these correctly because /comments is a longer, more specific path — but it’s worth knowing this works by path specificity, not registration order. No action needed, just awareness.


5. schemas.py

- 1. UserPayload exposes internal fields that shouldn’t be public.
role, status, karma, post_count, comment_count, and last_active_at are all present. Some of these are fine as public profile data, but role exposes whether a user is a moderator or admin — which is information an attacker can use to target privileged accounts. status exposes whether an account is suspended or banned, which leaks moderation decisions.
Check every place UserPayload is serialized in route responses. If it’s used in the /auth/me response (your own profile), all fields are fine. If it’s ever used to represent another user’s profile in a public context, role and status should be omitted or gated.
2. PostPayload exposes url_normalized and is_ingested publicly.
url_normalized is your internal deduplication key — clients don’t need it to render a post. is_ingested is an internal content pipeline flag. Neither belongs in a public API response. Remove them from PostPayload and keep them internal. If you ever need them for admin/moderator views, create a separate PostAdminPayload that extends PostPayload.


3. PostVotePayload and CommentVotePayload are structurally identical.
Both have exactly the same five fields: id, upvote_count, downvote_count, score, rank_score, viewer_vote. They’re separate classes purely because one wraps a post and one wraps a comment, which is fine for response envelope clarity — but the payload itself could be a shared VotePayload base class that both extend (even with no additional fields), making the intent explicit and reducing duplication if the vote response shape ever gains a field.
4. model_config = ConfigDict(from_attributes=True) is repeated on every class.
Twelve classes all set the same config. Define a shared base:

```python
class _Base(BaseModel):
    model_config = ConfigDict(from_attributes=True)
```

- Then all schemas inherit from _Base instead of BaseModel. One config declaration, one place to update if it ever changes.
5. CommentPayload is missing viewer_can_edit context for deleted/removed comments.
viewer_can_edit is present on CommentPayload, which is correct. But CommentPayload also exposes status — if a comment is not active, viewer_can_edit should always be false. This is enforced in reads.py via _viewer_can_edit, so the schema itself is just a mirror of whatever the service sends. The risk is that if another code path serializes a CommentPayload without going through _viewer_can_edit, the flag could be wrong. Not a schema bug, but worth a note.


Minor Points
PageInfoPayload has from_attributes=True but is constructed from a dataclass (PageInfo), not a SQLAlchemy model. Pydantic handles dataclasses fine with from_attributes=True via model_validate, so this works — but it’s worth knowing that from_attributes=True is doing real work here for the dataclass-to-schema conversion, not just being cargo-culted.
viewer_vote: int | None on vote payloads accepts any integer in theory. Since viewer_vote should only ever be 1, -1, or null, constraining the type to Literal[1, -1] | None would make the schema self-documenting and catch any accidental value leaking from the service layer.
Datetime fields have no timezone enforcement. Pydantic v2 will serialize datetime objects as-is. If your service layer ever returns a naive datetime (no tzinfo), the serialized response will be timezone-ambiguous. Constraining to AwareDatetime from pydantic would catch this at the boundary.




## Bounded Query Patterns

- the feed queries are correctly bounded via the `limit + 1` fetch pattern.

```python
query = _apply_feed_cursor(...).limit(limit + 1)
posts = result.scalars().unique().all()
has_next_page = len(posts) > limit
posts = posts[:limit]
```

- this is the right approach — fetch one extra to detect the next page without a separate count query. the slicing before passing to `_feed_page_info` is correct but order-dependent as flagged earlier.

- the gap is `get_post_comments`. it has no limit at all:

```python
result = await db.execute(query)
comments = result.scalars().unique().all()
```

- no `limit`, no cursor, no cap. this is the only unbounded query in the read layer and it’s a real risk — a post with hundreds of comments returns everything in one shot. the `CommentPage` always returns `has_next_page=False` and `next_cursor=None`, confirming this is intentional for now, but there should at least be a hardcoded safety ceiling like .limit(500) until proper pagination is added. clarify??

- the viewer vote queries are bounded correctly — `_viewer_post_votes` uses `IN` against the already-sliced page of post IDs, so it’s bounded by `limit`.
- `_viewer_comment_votes` is bounded by however many comments were returned, which loops back to the unbounded comment query problem.


## Opaque Cursor Handling

- the encode/decode pair is solid:

```python
def encode_feed_cursor(payload: dict[str, str | float]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")
```

- `sort_keys=True` ensures deterministic encoding — two logically identical cursors always produce the same string.
- `urlsafe_b64encode` is the right choice over standard base64 for a URL query parameter. the cursor is opaque to clients and carries its own kind field for validation.

- `decode_feed_cursor` validates the `kind` field on decode:

```python
if not isinstance(payload, dict) or payload.get("kind") != kind:
    raise ReadError(400, "validation_error", "Cursor is invalid.")
```

- this prevents a `new` feed cursor from being accepted on the `top` feed, which is correct. 

- the gap is the `pragma: no cover` on the exception handler. The base64/JSON parse failure path is a real client-reachable code path — a malformed cursor from a client should hit this. That coverage skip should be removed and the path should be tested. is this handled in our code??

- the second gap is no cursor payload field validation. after decoding, the code does:

```python
cursor_id = UUID(str(payload["id"]))
rank_score = float(payload["rank_score"])
submitted_at = datetime.fromisoformat(str(payload["submitted_at"]))
```

- if the decoded payload is missing `id`, `rank_score`, or `submitted_at`, these lines raise a raw `KeyError` or `ValueError` that bypasses `ReadError` and will surface as a 500. perhaps we can wrap the field extraction in the same try/except that wraps the decode, or validate required keys explicitly before accessing them.

## Top Feed Ordering

- the ordering is correctly applied:

```python
if kind == "top":
    query = query.order_by(desc(Post.rank_score), desc(Post.id))
```

- `rank_score desc`, `id desc` matches the locked spec. the `id desc` tiebreaker is correct - it ensures deterministic ordering when two posts share the same rank score. 

- the cursor application for `top` has a float equality problem:

```python
return query.where(
    or_(
        Post.rank_score < rank_score,
        and_(Post.rank_score == rank_score, Post.id < cursor_id),
    )
)
```

- the `Post.rank_score = rank_score` comparison is a float equality in SQL. PostgreSQL stores `FLOAT / DOUBLE PRECISION` with binary precision, and the value we encoded in the cursor may not round-trip to exactly the same binary representation when decoded from JSON as a Python `float`. 
- this means the tie-breaking branch (`rank_score == rank_score AND id < cursor_id`) may never fire for posts that should be in the same tie group, causing those rows to be silently skipped across pages.

- i think a good fix is to store and compare `rank_score` as `NUMERIC` in the schema, or to encode the cursor rank score as a string representation with sufficient decimal places and use a small epsilon range in the comparison. The most robust fix is making `rank_score` a `NUMERIC` column so equality is exact.


## Jobs Filtering by Expiry

```python
query = query.where(
    Post.post_type == PostType.JOB,
    or_(Post.job_expires_at.is_(None), Post.job_expires_at > now),
).order_by(desc(Post.submitted_at), desc(Post.id))
```

- both expiry conditions are correctly handled — `NULL` expiry (no expiry date, always visible) and `> now` (future expiry, visible). The now value is derived from `_utcnow()` which uses `datetime.now(UTC)`, so it’s timezone-aware and consistent with how PostgreSQL stores timestamptz.

- one subtle issue: `now` is captured once at the start of `_get_feed` and reused. In practice this is fine — the entire query executes in milliseconds. But if connection pool latency is ever significant, there’s a tiny window where a job could expire between `now` being captured and the query executing. This is theoretical for a v1 platform.

- the jobs feed cursor reuses the `submitted_at` path, which is correct and consistent with `new`. The `kind="jobs"` field in the cursor payload prevents cross-feed cursor reuse. Clean.


## Flat Comments Response

```python
query = (
    select(Comment)
    .options(joinedload(Comment.author))
    .where(
        Comment.post_id == post_id,
        Comment.status == CommentStatus.ACTIVE,
    )
)
```

- the query correctly fetches all active comments for the post in a flat list. `parent_comment_id` and `depth` are fields on `CommentRead`, so the client has everything needed for tree reconstruction. The author is eager-loaded via `joinedload` to avoid N+1 on author resolution.

- the sort implementation is correct for all three cases:

```python
if sort == "top":
    query = query.order_by(desc(Comment.rank_score), desc(Comment.id))
elif sort == "new":
    query = query.order_by(desc(Comment.created_at), desc(Comment.id))
else:
    query = query.order_by(Comment.created_at, Comment.id)
```

- all three have `id` as a tiebreaker, which ensures stable ordering. `old` uses ascending order on both, which is correct.

- the gap is that deleted/removed comments are filtered out entirely (`Comment.status = CommentStatus.ACTIVE`). this means if a parent comment is removed, its replies still appear in the flat list with a `parent_comment_id` pointing to a comment that isn’t in the response. 
- client-side tree reconstruction will encounter orphaned replies with no parent to attach to. - - this is a product decision — HN shows [deleted] placeholders for removed comments — but the current behaviour silently breaks thread continuity. Worth a deliberate note in the code even if the behaviour stays as-is for now. perhaps we can have something similar like HN [deleted].


## Viewer-Aware Fields

- the viewer enrichment strategy is correct and disciplined:
	- Feeds: single second query using `IN` against the page of post IDs — bounded, one round trip.
	- Post detail: single scalar query for the specific post/user pair — minimal.
	- Comments: single second query using `IN` against returned comment IDs — bounded by comment count.

- the unauthenticated path short-circuits cleanly:

```python
if viewer_user_id is None or not post_ids:
    return {}
```

- no unnecessary DB round trips for public reads.

- `viewer_can_edit` and `viewer_can_moderate` are derived in `_viewer_can_edit` and `_viewer_can_moderate` — pure Python, no extra queries. The logic is:

```python
def _viewer_can_edit(*, viewer_user_id, author_id, status) -> bool:
    return viewer_user_id == author_id and status in {PostStatus.ACTIVE, CommentStatus.ACTIVE}
```

- this has the enum comparison bug flagged in the reads review — if `PostStatus` and `CommentStatus` are separate Python enums, the mixed set comparison will always miss one type. 

- this is the highest priority fix in the entire read layer.

- `viewer_can_moderate` correctly checks for both `MODERATOR` and `ADMIN` roles:

```python
def _viewer_can_moderate(viewer_role: UserRole | None) -> bool:
    return viewer_role in {UserRole.MODERATOR, UserRole.ADMIN}
```

- Clean. the `None` case is handled correctly by the `in` check returning `False`.

1. Data flow from service to wire — `reads.py` returns dataclasses (`PostRead`, `CommentRead`, `FeedPage`, `CommentPage`). `schemas.py` must deserialize those via `model_validate` with `from_attributes=True`. Whether every field name and type actually aligns across that boundary hasn’t been verified.

2. The manual dict wrapping pattern — routes construct `{"post": await get_post_detail(...)}` and pass it to `PostResponse.model_validate(...)`. This is a fragile pattern — if the envelope key ever mismatches the schema field name, Pydantic silently sets the field to `None` rather than raising unless the field is required.

3. Viewer context propagation chain — how `CurrentSession` flows from `dependencies.py` → route → `_viewer_context` → service function → `_serialize_post`/`_serialize_comment`, and whether anything is lost or mistyped along that chain.

4. Error propagation — how `ReadError` raised in `reads.py` surfaces through the route back to `read_error_handler` in `errors.py`.