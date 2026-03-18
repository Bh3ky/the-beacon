## FEEDBACK ON PHASE 3 CORE API PLAN


my feedback and what we need to lock in on:

### 1. `user_sessions` table strategy

- on the `user_sessions` we need to decide the kind of session we will be running - is it database-backed opaque token, signed JWT token or hybrid. this will determine how GET /auth/me resolves the current user, whether logout is a real invalidation or client-side delete, and whther session revocation (e.g., "log out all devices") is even possible.

    - if we were to use JWTs with no server-side record then our "session invalidation" on logout would be flawed. 

MY RECOMMENDATION: use DB-backed sessions with an opaque token. WHY?? this will make sure we have the ability to revoke sessions (and not have those situations where people log into other people's accounts)

NOTES ON IMPLEMENTATION: perhaps `user_sessions` table should store

```python
# The session token the client holds is a random opaque string
# The DB stores a hash of it — never the raw token
session_token_hash: str   # sha256(raw_token), indexed
user_id: UUID
created_at: datetime
last_seen_at: datetime
expires_at: datetime
user_agent: str | None
ip_address: str | None
```

on login:

```python
import secrets, hashlib

raw_token = secrets.token_urlsafe(32)
token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
# store token_hash in DB, send raw_token in HttpOnly cookie
```

- on every authenticated request, the FastAPI dependency hashes the incoming cookie value and looks it up - never storing or comparing the raw token directly. this means a DB breach doesn't expose valid session tokens

on logout: delete the session row. instantly invalid. on "log out all devices": delete all rows for that `user_id`

session dependency in FastAPI:

```python
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    raw_token = request.cookies.get("session")
    if not raw_token:
        raise HTTPException(status_code=401)
    
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    session = await db.scalar(
        select(UserSession)
        .where(UserSession.token_hash == token_hash)
        .where(UserSession.expires_at > func.now())
    )
    if not session:
        raise HTTPException(status_code=401)
    
    return await db.get(User, session.user_id)
```

- on DB hit per protected request. later on we can cache the session lookup in Redis if we need to in v2 or not. 

---

### 2. CSRF strategy needs to be pinned on here

MY RECOMMENDATION: double-submit cookie pattern, tied to the session (whatttt???)

- since we are on a Next.js frontend + FastAPI backend with cookie-based auth, the double-submit pattern is the right fit (open for debate)

NOTES ON IMPLEMENTATION:

on login (alongside the session cookie): 

```python
import secrets, hmac

csrf_token = secrets.token_hex(32)
# Store csrf_token (or its hash) on the session row
# Also set it as a readable (non-HttpOnly) cookie
response.set_cookie(
    "csrf_token",
    csrf_token,
    httponly=False,   # JS must be able to read this
    secure=True,
    samesite="strict",
    max_age=86400
)
```

FastAPI validation dependency:

```python
async def validate_csrf(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    header_token = request.headers.get("X-CSRF-Token")
    cookie_token = request.cookies.get("csrf_token")
    
    if not header_token or not cookie_token:
        raise HTTPException(status_code=403, detail="CSRF validation failed")
    
    if not hmac.compare_digest(header_token, cookie_token):
        raise HTTPException(status_code=403, detail="CSRF validation failed")
```

NOTE: use `hmac.compare_digest -- not =-- to prevent timing attacks

apply it only to mutating routes:

```python
@router.post("/posts", dependencies=[Depends(validate_csrf)])
async def create_post(...): ...
```

on the Next.js side, our Axios interceptor reads the `csrf_token` cookie and injects it as `X-CSRF-Token` on every non-GET request. since we already have the Zustand-based interceptor plan from Phase 2 we just wire it to this cookie name. 

we also add Origin validation as a second layer:

```python
ALLOWED_ORIGINS = {"https://domain.com", "http://localhost:3000"}

@app.middleware("http")
async def validate_origin(request: Request, call_next):
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origin = request.headers.get("origin")
        if origin not in ALLOWED_ORIGINS:
            return Response(status_code=403)
    return await call_next(request)
```

- CSRF token + Origin check together is belt-and-suspenders. Note: either alone has edge cases.

### 3. Email canonicalization 

- we need to lock this in because if we are to continue and implement POST /auth/register without a settled canonicalization policy, we will end up getting duplicate accounts and subtle login failures in QA. examples" foo@Gmail.COM and foo@gmail.com

MY RECOMMENDATION: lowercase everything, no dot-stripping

```python
def canonicalize_email(raw: str) -> str:
    raw = raw.strip().lower()
    local, _, domain = raw.partition("@")
    if not domain:
        raise ValueError("Invalid email")
    return f"{local}@{domain}"
```

- lowercase the full address - both local part and domain. RFC 5321 says the local part is technically case-sensitive, but no real mail provider treats it that way, and it’s the source of 99% of duplicate account bugs.

- don't strip dots or + aliases -- Gmail ignores dots and + tags, but other providers don't.  If you strip them, you’ll incorrectly merge accounts on non-Gmail domains. The right answer for + aliases is to let them register as distinct accounts — that’s what most platforms do.

- we apply canonicalization at the service layer, not in the Pydantic schema. the schema validates format; the service normalizes before DB write and lookup. this means every login lookup also canonicalises before querying, so the comparison is always apples-to-apples. 

- finally, we need to add a `UNIQUE` constraints on the `email` column if we haven't, using the canonicalised value. Note: we don't rely on application-level uniqueness checks alone. 


4. "read-only" part

i see you pointed them out as lower-risk than writes. feed endpoints carry their own risks:

    - N+1 query exposure - /feeds/top with eager-loaded posts, vote counts, and author data is a performance trap if your query layer is not disciplined. 
    - unauthenticated access leaking draft/private content - if posts ever have visibility states, the read paths need permissions awareness from day one. 
    - pagination shape decisions that are hard to change - cursor vs offset, response envelope shape. 

MY RECOMMENDATION: 

- on N+1: the classic trap for a feed endpoint is loading posts, then for each post firing a separate query for the author, vote count, and comment count. At 25 posts per page that's potentially 75+ queries.
    - we can fix this at the query layer with explicit joins and subqueries:

```python
from sqlalchemy import select, func, outerjoin

vote_count = (
    select(func.count())
    .where(Vote.post_id == Post.id)
    .correlate(Post)
    .scalar_subquery()
    .label("vote_count")
)

comment_count = (
    select(func.count())
    .where(Comment.post_id == Post.id)
    .correlate(Post)
    .scalar_subquery()
    .label("comment_count")
)

stmt = (
    select(Post, User, vote_count, comment_count)
    .join(User, Post.author_id == User.id)
    .order_by(Post.score.desc())
    .limit(limit)
    .offset(offset)
)
```

    - one query. everything we need for the feed card comes back in a single round-trip. 

- on pagination: we can use cursor-based pagination for feeds over offset. WHY?? offset breaks: `OFFSET 50` on a live feed means “skip the first 50 rows at query time” — but if 3 new posts were inserted since page 1, the user sees duplicates or skips items. Cursor-based pagination is stable:

```python
# Request: GET /feeds/top?cursor=<encoded_last_post_id>&limit=25
# Response includes next_cursor if more results exist

def encode_cursor(post_id: UUID, score: float) -> str:
    import base64, json
    payload = json.dumps({"id": str(post_id), "score": score})
    return base64.urlsafe_b64encode(payload.encode()).decode()

# Query uses WHERE (score, id) < (cursor_score, cursor_id)
# instead of OFFSET
```

- for jobs feed, offset pagination may be acceptable if it's lower-velocity page. BUT BUT we need to stay consistent with the envelope shape regardless:

```json
{
  "items": [...],
  "next_cursor": "eyJpZCI6ICI...",
  "has_more": true
}
```


5. "ranking-trigger hooks" is a bit vague we need to clarify and lock on this

- if our ranking score technique were to depend on both vote counts and post age i.e needing to be recomputed on a schedule, not just on vote events then if we are to implement background worker + Redis cache for this, the worker needs to exist before slice 4 tests can be meaningful. (did we note this down in the api_spec.md file??)


- we need to have rate limiting on registration and login endpoints as these are highest-value targets for abuse. even a simple in-process rate limiter like slowapi should be considered in slice 1 scope. 

- note: we need to make sure in the auth security contract the checkpoint list map to actual pytest markers or CI gates, not just a mental checklist. 


MY RECOMMENDATION: on rate limiting we use slowapi for now, then use Redis-backed when we need distribution. 

- `slowapi` wraps `limits` and integrates cleanly with FastAPI

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

- apply tighter limits to auth routes specifically:

```python
python@router.post("/auth/register")
@limiter.limit("5/minute")
async def register(request: Request, ...): ...

@router.post("/auth/login")
@limiter.limit("10/minute")
async def login(request: Request, ...): ...
```

feed and read routes can be more generous as they are not abuse targets.

Sidenote on switching to Redis if need be: when w’re ready to scale or run multiple workers: slowapi supports a Redis storage backend via limits, so the migration path is just swapping the storage config, not rewriting our decorators. Since we already have Upstash Redis in your stack, this is a natural fit.

One additional note: for vote endpoints (Slice 4), we should consider a per-user rate limit in addition to per-IP. IP-based limits are bypassable; combining both makes abuse meaningfully harder.



- The /feeds/top Performance Trap
In Slice 2 and Slice 4, you mention aggregate count updates and ranking triggers. Calculating the "Top" feed algorithmically on the fly for every GET /feeds/top request will quickly bring your database to its knees as traffic grows.