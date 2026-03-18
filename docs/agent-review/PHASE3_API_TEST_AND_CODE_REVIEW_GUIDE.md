# PHASE3_API_TEST_AND_CODE_REVIEW_GUIDE.md

## Purpose

This file is the follow-along guide for validating the completed Phase 3 core API implementation.

It covers:

1. automated test execution
2. manual API validation
3. auth/session verification
4. feed/read verification
5. post/comment creation verification
6. voting verification
7. code-review checkpoints by file area

Use this after the Phase 3 slices are implemented.

---

## Phase 3 Scope Covered

This guide assumes the following are implemented:

- auth/session foundation
- verification-first registration
- resend verification
- login/logout/me
- top/new/jobs feeds
- post detail and flat comments
- post creation
- comment creation
- post voting
- comment voting

Current focused test baseline:

- `97 passed`

---

## Preconditions

Before following this guide, make sure:

1. Docker is running.
2. Local Postgres is started through Docker, not through a conflicting local Postgres app on port `5432`.
3. Your `.env` points at the Docker-backed database.
4. Migrations are applied.

Recommended terminal checks:

```bash
npm run db:up
npm run db:upgrade
psql "postgresql://postgres:postgres@127.0.0.1:5432/rifthub" -c "\dt"
```

Expected:

- the Phase 2 and Phase 3 tables exist
- `users`, `user_sessions`, `user_verification_tokens`, `posts`, `comments`, `post_votes`, and `comment_votes` are present

---

## Test Run Order

Follow this order:

1. run the focused automated suite
2. start the API in local development mode
3. validate auth/session flows
4. validate read endpoints
5. validate creation endpoints
6. validate vote endpoints
7. review the touched code areas

---

## Step 1: Run The Focused Automated Suite

From the repo root:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --package rifthub-api pytest \
  apps/api/tests/test_voting_helpers.py \
  apps/api/tests/test_voting_routes.py \
  apps/api/tests/test_creation_helpers.py \
  apps/api/tests/test_creation_routes.py \
  apps/api/tests/test_reads_helpers.py \
  apps/api/tests/test_reads.py \
  apps/api/tests/test_auth_security.py \
  apps/api/tests/test_auth_delivery.py \
  apps/api/tests/test_auth.py \
  apps/api/tests/test_config.py \
  apps/api/tests/test_schema_metadata.py \
  apps/api/tests/test_health.py \
  apps/api/tests/test_db_session.py
```

Expected:

- suite passes cleanly
- current expected result is `97 passed`

If this fails, stop and fix the regression before doing manual checks.

---

## Step 2: Start The API For Manual Testing

For local manual auth testing, use logging-based verification delivery so you can see the verification link directly in API logs:

```bash
RIFTHUB_VERIFICATION_DELIVERY_MODE=log npm run api:dev
```

Keep this terminal open.

Expected startup behavior:

- no traceback
- database ping succeeds
- API stays running

Health check from a second terminal:

```bash
curl http://127.0.0.1:8000/health
```

Expected JSON:

```json
{"service":"api","status":"ok","environment":"development"}
```

---

## Step 3: Prepare A Cookie Jar For Manual API Calls

In a second terminal:

```bash
rm -f /tmp/rifthub-cookies.txt
touch /tmp/rifthub-cookies.txt
```

You will reuse this file for:

- session cookie
- CSRF cookie

Helper command to read the CSRF cookie value:

```bash
awk '$6 == "rifthub_csrf" {print $7}' /tmp/rifthub-cookies.txt
```

Note:

- this assumes the CSRF cookie name is still `rifthub_csrf`
- if the cookie name changes in config, update the extractor accordingly

---

## Step 4: Auth Flow Validation

### 4.1 Register A New Pending Account

Use a unique email each run:

```bash
curl -i -c /tmp/rifthub-cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"username":"phase3user02","email":"phase3user+02@example.com","password":"avery-strong-password"}' \
  http://127.0.0.1:8000/v1/auth/register
```

Expected:

- `201 Created`
- body contains `"verification_required": true`
- returned user has `"status": "pending"`
- no authenticated session cookie is issued yet

### 4.2 Verify Login Is Blocked Before Verification

```bash
curl -i \
  -H "Content-Type: application/json" \
  -d '{"email":"phase3user+02@example.com","password":"avery-strong-password"}' \
  http://127.0.0.1:8000/v1/auth/login
```

Expected:

- `403`
- error code `account_pending_verification`

### 4.3 Get The Verification Token Locally

Because the API is running with `RIFTHUB_VERIFICATION_DELIVERY_MODE=log`, the API terminal should log a line like:

```text
Verification link for phase3user02 (phase3user+02@example.com): http://localhost:3000/verify?token=...
```

Copy the raw token value from the query string.

If you prefer Mailpit later, switch delivery mode to `mailpit` and read the same link from the mailbox UI instead.

### 4.4 Verify The Account

Replace `<TOKEN>` with the copied value:

```bash
curl -i -c /tmp/rifthub-cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"token":"<TOKEN>"}' \
  http://127.0.0.1:8000/v1/auth/verify
```

Expected:

- `200 OK`
- returned user has `"status": "active"`
- response sets:
  - `rifthub_session`
  - `rifthub_csrf`

### 4.4.1 Reject Garbage Verification Token

```bash
curl -i \
  -H "Content-Type: application/json" \
  -d '{"token":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}' \
  http://127.0.0.1:8000/v1/auth/verify
```

Expected:

- non-success response
- current implementation returns `400 verification_token_invalid`

### 4.4.2 Reject Used Verification Token

Resubmit the same token from Step 4.4:

```bash
curl -i \
  -H "Content-Type: application/json" \
  -d '{"token":"<TOKEN>"}' \
  http://127.0.0.1:8000/v1/auth/verify
```

Expected:

- non-success response
- current implementation returns `409 conflict`

### 4.4.3 Resend Verification Before Verification Completes

Run this before Step 4.4 if you want to validate the pending-account resend path:

```bash
curl -i \
  -H "Content-Type: application/json" \
  -d '{"email":"phase3user+02@example.com"}' \
  http://127.0.0.1:8000/v1/auth/resend-verification
```

Expected:

- `204 No Content`

### 4.4.4 Resend Verification After Verification

After Step 4.4, run the same resend call again:

```bash
curl -i \
  -H "Content-Type: application/json" \
  -d '{"email":"phase3user+02@example.com"}' \
  http://127.0.0.1:8000/v1/auth/resend-verification
```

Expected:

- `204 No Content`
- current behavior is a safe no-op for already-active accounts

### 4.5 Confirm Authenticated Identity

```bash
curl -i -b /tmp/rifthub-cookies.txt \
  http://127.0.0.1:8000/v1/auth/me
```

Expected:

- `200 OK`
- correct user payload

### 4.6 Confirm Logout Is CSRF-Protected

Without CSRF header:

```bash
curl -i -b /tmp/rifthub-cookies.txt -X POST \
  http://127.0.0.1:8000/v1/auth/logout
```

Expected:

- `403`
- message `CSRF validation failed.`

Now with the CSRF header:

```bash
CSRF_TOKEN="$(awk '$6 == "rifthub_csrf" {print $7}' /tmp/rifthub-cookies.txt)"
curl -i -b /tmp/rifthub-cookies.txt -c /tmp/rifthub-cookies.txt \
  -X POST \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  http://127.0.0.1:8000/v1/auth/logout
```

Expected:

- `204 No Content`
- cookies cleared

### 4.6.1 Confirm The Old Session Cookie Is Invalid

Before logout, copy the old session value from `/tmp/rifthub-cookies.txt`. After logout, try:

```bash
curl -i -b "rifthub_session=<OLD_SESSION_VALUE>" \
  http://127.0.0.1:8000/v1/auth/me
```

Expected:

- `401 unauthenticated`

### 4.7 Log Back In

```bash
curl -i -b /tmp/rifthub-cookies.txt -c /tmp/rifthub-cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"email":"phase3user+02@example.com","password":"avery-strong-password"}' \
  http://127.0.0.1:8000/v1/auth/login
```

Expected:

- `200 OK`
- auth cookie set again
- CSRF cookie set again

Refresh the shell variable after login:

```bash
CSRF_TOKEN="$(awk '$6 == "rifthub_csrf" {print $7}' /tmp/rifthub-cookies.txt)"
```

---

## Step 5: Read Endpoint Validation

### 5.1 Top Feed

```bash
curl -i http://127.0.0.1:8000/v1/feeds/top
```

Expected:

- `200 OK`
- response has:
  - `items`
  - `page_info.next_cursor`
  - `page_info.has_next_page`
- unauthenticated viewer fields should be neutral:
  - `viewer_vote = null`
  - `viewer_can_edit = false`
  - `viewer_can_moderate = false`

### 5.2 New Feed

```bash
curl -i http://127.0.0.1:8000/v1/feeds/new
```

Expected:

- `200 OK`
- same collection envelope as top feed

### 5.3 Jobs Feed

```bash
curl -i http://127.0.0.1:8000/v1/feeds/jobs
```

Expected:

- `200 OK`
- jobs-only payload shape

### 5.3.1 Manual Pagination Spot Check

If you have enough posts to get `has_next_page = true`, follow the cursor:

```bash
curl -i "http://127.0.0.1:8000/v1/feeds/top?limit=1"
curl -i "http://127.0.0.1:8000/v1/feeds/top?limit=1&cursor=<NEXT_CURSOR>"
```

Expected:

- second page uses the returned cursor cleanly
- no duplicate item from page one
- ordering remains stable

### 5.4 Post Detail

Use a real post id created in Step 6 after you have one:

```bash
curl -i http://127.0.0.1:8000/v1/posts/<POST_ID>
```

Expected:

- `200 OK`
- `post.viewer_vote` is present
- `post.viewer_can_edit` is present
- unauthenticated request should still show:
  - `viewer_vote = null`
  - `viewer_can_edit = false`
  - `viewer_can_moderate = false`

### 5.5 Post Comments

```bash
curl -i "http://127.0.0.1:8000/v1/posts/<POST_ID>/comments?sort=top"
```

Expected:

- `200 OK`
- flat comment list
- each item includes:
  - `parent_comment_id`
  - `depth`
- `page_info.next_cursor` is `null`
- `page_info.has_next_page` is `false`

Also spot-check:

```bash
curl -i "http://127.0.0.1:8000/v1/posts/<POST_ID>/comments?sort=new"
curl -i "http://127.0.0.1:8000/v1/posts/<POST_ID>/comments?sort=old"
```

Expected:

- both return `200 OK`
- ordering changes appropriately

---

## Step 6: Post And Comment Creation Validation

### 6.1 Create A Text Post

```bash
curl -i -b /tmp/rifthub-cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  -d '{"post_type":"text","category":"ask","title":"Phase 3 text post","body_markdown":"Text body for manual validation."}' \
  http://127.0.0.1:8000/v1/posts
```

Expected:

- `201 Created`
- response contains `post`
- `post.status` is `active`
- `post.slug` is present

Save the returned `post.id` as `<POST_ID>`.

Recommended:

```bash
export POST_ID=<id from response>
```

### 6.2 Create A Link Post

```bash
curl -i -b /tmp/rifthub-cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  -d '{"post_type":"link","category":"ecosystem","title":"Phase 3 link post","url":"https://example.com/rifthub-phase3-story-02"}' \
  http://127.0.0.1:8000/v1/posts
```

Expected:

- `201 Created`
- `post.url_normalized` is present
- `post.domain` is present

### 6.3 Verify Duplicate Link Protection

Repeat the same link-post request.

Expected:

- `409 Conflict`
- error code `duplicate_submission`

### 6.4 Create A Top-Level Comment

```bash
curl -i -b /tmp/rifthub-cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  -d '{"body_markdown":"Top-level comment for manual validation."}' \
  http://127.0.0.1:8000/v1/posts/<POST_ID>/comments
```

Expected:

- `201 Created`
- `comment.depth` is `0`

Save the returned `comment.id` as `<COMMENT_ID>`.

Recommended:

```bash
export COMMENT_ID=<id from response>
```

### 6.5 Create A Reply

```bash
curl -i -b /tmp/rifthub-cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  -d '{"body_markdown":"Reply for manual validation.","parent_comment_id":"<COMMENT_ID>"}' \
  http://127.0.0.1:8000/v1/posts/<POST_ID>/comments
```


Expected:

- `201 Created`
- `comment.depth` is `1`

### 6.5.1 Reject Cross-Post Parent Injection

Create a second post and a comment under it, then try to use that second post's comment id as the parent while posting under the first post:

```bash
curl -i -b /tmp/rifthub-cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  -d '{"body_markdown":"Injected reply","parent_comment_id":"<COMMENT_ID_FROM_OTHER_POST>"}' \
  http://127.0.0.1:8000/v1/posts/<POST_ID>/comments
```

Expected:

- non-success response
- current implementation returns `404 comment_not_found`

### 6.6 Confirm Read Surface Sees The New Content

```bash
curl -i http://127.0.0.1:8000/v1/posts/<POST_ID>
curl -i "http://127.0.0.1:8000/v1/posts/<POST_ID>/comments?sort=top"
```

Expected:

- post detail returns the created post
- comment list includes the top-level comment and reply

### 6.7 Expired Job Spot Check

Create a job with a past expiry:

```bash
curl -i -b /tmp/rifthub-cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  -d '{"post_type":"job","category":"jobs","title":"Expired job","body_markdown":"Should not show in jobs feed","job_expires_at":"2020-01-01T00:00:00Z"}' \
  http://127.0.0.1:8000/v1/posts
```

Then check:

```bash
curl -i http://127.0.0.1:8000/v1/feeds/jobs
```

Expected:

- expired job should not appear in the jobs feed

---

## Step 7: Voting Validation

### 7.1 Upvote A Post

```bash
curl -i -b /tmp/rifthub-cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  -d '{"vote_value":1}' \
  http://127.0.0.1:8000/v1/posts/<POST_ID>/vote
```

Expected:

- `200 OK`
- minimal post vote payload only
- `viewer_vote` is `1`

### 7.2 Repeat The Same Upvote

Run the same request again.

Expected:

- `200 OK`
- same final payload
- vote state remains `viewer_vote = 1`

### 7.3 Flip Post Vote To `-1`

```bash
curl -i -b /tmp/rifthub-cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  -d '{"vote_value":-1}' \
  http://127.0.0.1:8000/v1/posts/<POST_ID>/vote
```

Expected:

- `200 OK`
- `viewer_vote` becomes `-1`
- score changes by `-2` relative to the prior `+1` state
- concretely:
  - `upvote_count` decreases by `1`
  - `downvote_count` increases by `1`
  - `score` decreases by `2`

### 7.4 Remove The Post Vote

```bash
curl -i -b /tmp/rifthub-cookies.txt \
  -X DELETE \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  http://127.0.0.1:8000/v1/posts/<POST_ID>/vote
```

Expected:

- `200 OK`
- `viewer_vote` is `null`

### 7.5 Remove The Missing Post Vote Again

Run the same delete again.

Expected:

- `200 OK`
- unchanged final state

### 7.6 Upvote A Comment

```bash
curl -i -b /tmp/rifthub-cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  -d '{"vote_value":1}' \
  http://127.0.0.1:8000/v1/comments/<COMMENT_ID>/vote
```

Expected:

- `200 OK`
- minimal comment vote payload only
- `viewer_vote` is `1`

Note:

- self-voting is currently allowed in this build
- that is an explicit current baseline, not an accidental omission

### 7.7 Remove The Comment Vote

```bash
curl -i -b /tmp/rifthub-cookies.txt \
  -X DELETE \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  http://127.0.0.1:8000/v1/comments/<COMMENT_ID>/vote
```

Expected:

- `200 OK`
- `viewer_vote` is `null`

### 7.8 Remove The Missing Comment Vote Again

Repeat the same delete.

Expected:

- `200 OK`
- unchanged final state

---

## Step 8: Security Failure Checks

Run these as spot checks.

### 8.1 Mutating Route Without Auth

```bash
curl -i \
  -H "Content-Type: application/json" \
  -d '{"vote_value":1}' \
  http://127.0.0.1:8000/v1/posts/<POST_ID>/vote
```

Expected:

- `401 unauthenticated`

### 8.2 Mutating Route With Missing Or Wrong CSRF

```bash
curl -i -b /tmp/rifthub-cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: wrong-token" \
  -d '{"body_markdown":"Should fail"}' \
  http://127.0.0.1:8000/v1/posts/<POST_ID>/comments
```

Expected:

- `403`
- message `CSRF validation failed.`

### 8.3 Invalid Vote Value

```bash
curl -i -b /tmp/rifthub-cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  -d '{"vote_value":0}' \
  http://127.0.0.1:8000/v1/posts/<POST_ID>/vote
```

Expected:

- `422 validation_error`

### 8.4 Vote Missing Target

```bash
curl -i -b /tmp/rifthub-cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  -d '{"vote_value":1}' \
  http://127.0.0.1:8000/v1/posts/00000000-0000-0000-0000-000000000000/vote
```

Expected:

- `404 post_not_found`

---

## Step 9: Code Review Checklist

Review these areas in this order.

### 9.1 API Entry, Dependencies, And Error Handling

Inspect:

- [main.py](/Users/telasi/Developer/RiftHub/apps/api/src/rifthub_api/main.py)
- [dependencies.py](/Users/telasi/Developer/RiftHub/apps/api/src/rifthub_api/dependencies.py)
- [errors.py](/Users/telasi/Developer/RiftHub/apps/api/src/rifthub_api/errors.py)

Look for:

- thin route design
- exception handlers for each domain error
- fail-fast startup ping
- mutating-origin protection
- CSRF enforcement path

### 9.2 Auth And Delivery

Inspect:

- [auth.py](/Users/telasi/Developer/RiftHub/apps/api/src/rifthub_api/routes/auth.py)
- [service.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/auth/service.py)
- [security.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/auth/security.py)
- [delivery.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/auth/delivery.py)

Look for:

- verification-first registration
- pending users blocked from login
- idempotent logout
- resend-verification behavior
- session cookie and CSRF cookie split
- email canonicalization
- no plaintext verification token storage
- resend flow correctness

### 9.3 Read Layer

Inspect:

- [reads.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/reads.py)
- [feeds.py](/Users/telasi/Developer/RiftHub/apps/api/src/rifthub_api/routes/feeds.py)
- [posts.py](/Users/telasi/Developer/RiftHub/apps/api/src/rifthub_api/routes/posts.py)
- [schemas.py](/Users/telasi/Developer/RiftHub/apps/api/src/rifthub_api/schemas.py)

Look for:

- bounded query patterns
- opaque cursor handling
- top feed ordering by `rank_score desc, id desc`
- jobs filtering by expiry
- flat comments response
- viewer-aware fields

### 9.4 Creation Layer

Inspect:

- [creation.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/creation.py)
- [posts.py](/Users/telasi/Developer/RiftHub/apps/api/src/rifthub_api/routes/posts.py)

Look for:

- deterministic slug generation
- non-ASCII title behavior
- URL normalization
- safe domain upsert pattern
- duplicate link protection on `url_normalized`
- max comment depth enforcement
- SQL-side aggregate updates on comment creation

### 9.5 Voting Layer

Inspect:

- [voting.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/voting.py)
- [posts.py](/Users/telasi/Developer/RiftHub/apps/api/src/rifthub_api/routes/posts.py)
- [comments.py](/Users/telasi/Developer/RiftHub/apps/api/src/rifthub_api/routes/comments.py)
- [write_access.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/write_access.py)

Look for:

- explicit vote transition handling
- same-value re-vote no-op behavior
- delete-missing-vote success behavior
- one transaction per vote row change plus aggregate update
- active-target-only voting
- shared suspended/banned write restriction
- shared write guard called before write-side mutations
- post `rank_score` temporary synchronous refresh
- comment `rank_score = score`

### 9.6 Model And Schema Alignment

Inspect:

- [user.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/models/user.py)
- [verification.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/models/verification.py)
- [vote.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/models/vote.py)
- [post.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/models/post.py)
- [comment.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/models/comment.py)
- [types.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/db/types.py)

Look for:

- `pending` user status support
- verification token lifecycle shape
- unique vote constraints
- post/comment counter and integrity constraints
- schema assumptions matching route/service behavior

### 9.7 Test Coverage

Inspect:

- [test_auth.py](/Users/telasi/Developer/RiftHub/apps/api/tests/test_auth.py)
- [test_auth_delivery.py](/Users/telasi/Developer/RiftHub/apps/api/tests/test_auth_delivery.py)
- [test_auth_security.py](/Users/telasi/Developer/RiftHub/apps/api/tests/test_auth_security.py)
- [test_reads.py](/Users/telasi/Developer/RiftHub/apps/api/tests/test_reads.py)
- [test_reads_helpers.py](/Users/telasi/Developer/RiftHub/apps/api/tests/test_reads_helpers.py)
- [test_creation_routes.py](/Users/telasi/Developer/RiftHub/apps/api/tests/test_creation_routes.py)
- [test_creation_helpers.py](/Users/telasi/Developer/RiftHub/apps/api/tests/test_creation_helpers.py)
- [test_voting_routes.py](/Users/telasi/Developer/RiftHub/apps/api/tests/test_voting_routes.py)
- [test_voting_helpers.py](/Users/telasi/Developer/RiftHub/apps/api/tests/test_voting_helpers.py)

Look for:

- route happy paths
- auth and CSRF failures
- duplicate link protection
- jobs/read edge cases
- vote delta semantics
- delete-missing-vote symmetry

---

## Step 10: Exit Criteria

Phase 3 API validation is complete when all of the following are true:

1. focused automated suite passes
2. health check passes
3. register creates a pending account
4. verify activates the account and sets cookies
5. login/logout/me work correctly
6. top/new/jobs feeds respond with correct envelopes
7. post detail and flat comments respond correctly
8. post and comment creation succeed with valid CSRF and fail without it
9. duplicate link protection behaves correctly
10. post and comment voting support create, replace, delete, and delete-missing flows
11. code review over the listed files does not reveal boundary drift or obvious correctness issues

---

## Notes

- Production email delivery is still not live until domain + Resend setup is completed.
- For local manual auth testing, `RIFTHUB_VERIFICATION_DELIVERY_MODE=log` is the fastest path.
- If you switch to Mailpit later, keep the rest of this guide unchanged and only change how you retrieve the verification token.
- Cookie flag expectations differ by environment:
  - local dev over HTTP should not expect `Secure=True`
  - production/staging over HTTPS should expect `Secure=True`
