# Feedback Creation Layer

### Deterministic Slug Generation

- normalized[:MAX_SLUG_LENGTH].rstrip("-") could theoretically return an empty string if the first 100 characters are all hyphens, which the or "post" fallback catches. That’s correct. But a title like "---" (all punctuation) hits the pre-truncation fallback at if not normalized, which also produces "post". Both paths lead to the same fallback — clean.
The slug is not guaranteed unique, which is intentional per the locked spec. No issue there.


### Non-ASCII Title Behavior

```python
normalized = normalized.encode("ascii", "ignore").decode("ascii")
```

- This silently drops all non-ASCII characters. For an Africa-focused platform where titles in French, Swahili, Amharic, or Arabic are realistic, this means:
	∙	A title like "Développement au Sénégal" becomes "dveloppement-au-sngal" — mangled but not empty
	∙	A title entirely in Amharic script produces an empty string, hits the if not normalized fallback, and becomes "post"
	∙	All Amharic posts get the slug "post" — not globally unique but not enforced to be, so it’s technically within spec
This is a known limitation called out in the Slice 3 review. The current behaviour is safe and won’t crash, but it’s worth a comment in the code explicitly noting that non-ASCII titles may produce degraded or generic slugs, and that transliteration is a future improvement. As written, a reader might think this is an oversight rather than a deliberate v1 choice.


### URL Normalization

```python
def normalize_url(raw_url: str) -> str:
    split = _normalized_split(raw_url)
    scheme = split.scheme.lower()
    hostname = split.hostname.lower()
    port = split.port
    netloc = hostname
    if port is not None and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{hostname}:{port}"
    normalized = SplitResult(
        scheme=scheme,
        netloc=netloc,
        path=split.path,
        query=split.query,
        fragment=split.fragment,
    )
    return urlunsplit(normalized)
```

- Scheme and host lowercasing is correct. Default port stripping for 80/443 is correct. Whitespace trimming happens in _normalized_split via candidate = raw_url.strip().
Three gaps worth flagging:
1. The fragment is preserved in url_normalized. Fragments (#section) are client-side only — the server never sees them in a real HTTP request. Two URLs that differ only by fragment point to the same resource. https://example.com/story and https://example.com/story#comments will not deduplicate against each other. Strip the fragment before storing:

```python
normalized = SplitResult(scheme=scheme, netloc=netloc, path=split.path, query=split.query, fragment="")
```

2. The path is not normalized. https://example.com/story/ and https://example.com/story are the same resource on most servers but will deduplicate as different URLs. A trailing slash strip on the path (split.path.rstrip("/") or "/") would catch the most common case.

3. Query string parameter order is not normalized. https://example.com?b=2&a=1 and https://example.com?a=1&b=2 are the same URL but won’t deduplicate. This is harder to fix correctly (some parameters are order-sensitive) so deferring it is reasonable, but it should be noted.


### Safe Domain Upsert Pattern

```python
async def resolve_or_create_domain(*, db: AsyncSession, hostname: str) -> Domain:
    insert_stmt = (
        pg_insert(Domain)
        .values(hostname=hostname)
        .on_conflict_do_nothing(index_elements=[Domain.hostname])
    )
    await db.execute(insert_stmt)
    domain = await db.scalar(select(Domain).where(Domain.hostname == hostname))
    if domain is None:
        raise CreationError(500, "internal_error", "Failed to resolve domain.")
    return domain
```

- This is the correct pattern for the race condition called out in the Slice 3 review. INSERT ... ON CONFLICT DO NOTHING handles concurrent submissions with the same hostname — one wins the insert, the other silently does nothing, and both proceed to the SELECT. The defensive if domain is None guard after the select is correct — it should be unreachable if the unique constraint is in place, but it catches any unexpected DB state cleanly.
One issue: on_conflict_do_nothing(index_elements=[Domain.hostname]) passes a column object rather than a string. SQLAlchemy’s PostgreSQL insert dialect expects index_elements to be column names as strings or mapped column expressions. Using Domain.hostname (the mapped attribute) may or may not resolve correctly depending on your SQLAlchemy version. The safe form is:

```python
.on_conflict_do_nothing(index_elements=["hostname"])
```

- Verify this works in your test suite — if resolve_or_create_domain is tested under concurrent load, a misconfigured index_elements would silently fall back to inserting and failing on the unique constraint rather than doing nothing, which would surface as an integrity error rather than the clean 500.

## Duplicate link protection on url_normalized

```python
if payload.post_type == PostType.LINK and normalized_url is not None:
    existing_post = await db.scalar(
        select(Post).where(
            Post.status == PostStatus.ACTIVE,
            Post.url_normalized == normalized_url,
        )
    )
    if existing_post is not None:
        raise CreationError(
            409,
            "duplicate_submission",
            "This story has already been submitted recently.",
            details={
                "existing_post_id": str(existing_post.id),
                "existing_post_slug": existing_post.slug,
            },
        )
```

The logic is correct — checks against url_normalized (not raw URL), only for active posts, only for link type. The 409 response includes existing_post_id and existing_post_slug as specified.
Two gaps:
1. Job posts are not checked for duplicates. The duplicate check is gated on PostType.LINK only. A job post with a URL goes through URL normalization and domain resolution but skips the duplicate check. Two companies could submit the same job URL and both land as active posts. Whether this is intentional product policy should be explicit — either add a comment saying job duplicate detection is deferred, or extend the check to cover jobs.
2. There’s a race condition between the duplicate check and the insert. Two concurrent link post submissions with the same URL will both pass the SELECT check, both find no existing post, and both proceed to insert. One will succeed; the other will violate the unique constraint on url_normalized (assuming the constraint exists in the schema) and surface as an unhandled DB integrity error rather than a clean 409. This needs either a unique constraint plus an integrity error catch that re-raises as CreationError(409, ...), or a SELECT ... FOR UPDATE lock before the check.


- The cross-post parent injection check is correctly handled — the Comment.post_id == post_id condition in the parent lookup means a parent comment from another post returns 404 comment_not_found rather than allowing the cross-post link. Clean.
Depth computation is correct: depth = parent.depth + 1, checked against MAX_COMMENT_DEPTH before insert. The MAX_COMMENT_DEPTH: Final = 6 constant is defined at module level — correct, not a magic number inline.
One subtle issue: The depth check is depth > MAX_COMMENT_DEPTH, which means depth 7 is rejected but depth 6 is allowed. So the actual maximum is depth 6 (0-indexed), meaning 7 levels of nesting (root + 6 replies deep). Confirm this matches your intended product behaviour — if you want 6 levels of nesting total (root = level 0, max reply = level 5), the check should be depth >= MAX_COMMENT_DEPTH.

- The aggregate update uses Post.comment_count + 1 as a SQL expression — this is an atomic SQL-side increment, not a Python read-modify-write. Correct.
db.flush() before the aggregate update is correct — it ensures the comment row is written to the DB within the transaction before the post counter is updated, so both are visible atomically on commit.
One issue: now = _utcnow() is captured in Python and passed as last_commented_at. This is fine for consistency within the write path, but it means last_commented_at reflects Python application time rather than DB server time. If you ever run multiple API instances across servers with slight clock skew, last_commented_at values could be non-monotonic relative to created_at on the comment itself (which is likely DB-defaulted). Using func.now() from SQLAlchemy would make both timestamps come from the same clock. Not a critical issue for v1, but worth noting.
Both the comment insert and the post aggregate update are inside the same transaction (committed together with await db.commit()). This is correct — if the aggregate update fails, the whole transaction rolls back and the comment is not persisted.

- posts.py Changes Since Last Review
The previously flagged issues are now fixed:
	∙	_viewer_context now correctly returns tuple[UUID | None, UserRole | None]
	∙	sort now uses CommentSort imported from reads.py instead of an inline Literal
Still unresolved from the previous review: CreatePostRequest still has no field-level validation — empty title, whitespace-only title, past job_expires_at, and unbounded body length are all still accepted at the route boundary. The service layer catches empty title after stripping, but the route is still the better place for this.

