# DELTA_CHECKLIST.md

## Purpose

This checklist contains only the manual checks that became newly important after the Phase 3 API hardening pass.

Use this instead of rerunning the full [PHASE3_API_TEST_AND_CODE_REVIEW_GUIDE.md](/Users/telasi/Developer/RiftHub/docs/agent-review/PHASE3_API_TEST_AND_CODE_REVIEW_GUIDE.md) from scratch.

---

## Preconditions

Assume:

- the API is running locally
- Docker Postgres is up
- you already have at least one verified test account
- `/tmp/rifthub-cookies.txt` contains a valid logged-in session

Refresh your CSRF token variable first:

```bash
CSRF_TOKEN="$(awk '$6 == "rifthub_csrf" {print $7}' /tmp/rifthub-cookies.txt)"
```

---

## 1. Verification Token Edge Checks

### 1.1 Garbage Token

```bash
curl -i \
  -H "Content-Type: application/json" \
  -d '{"token":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}' \
  http://127.0.0.1:8000/v1/auth/verify
```

Expected:

- non-success response
- current behavior: `400 verification_token_invalid`

### 1.2 Reused Token

Resubmit a token you already used successfully:

```bash
curl -i \
  -H "Content-Type: application/json" \
  -d '{"token":"<USED_TOKEN>"}' \
  http://127.0.0.1:8000/v1/auth/verify
```

Expected:

- non-success response
- current behavior: `409 conflict`

---

## 2. Resend Verification Checks

### 2.1 Resend For A Pending Account

Use a pending account email:

```bash
curl -i \
  -H "Content-Type: application/json" \
  -d '{"email":"phase3user+02@example.com"}' \
  http://127.0.0.1:8000/v1/auth/resend-verification
```

Expected:

- `204 No Content`

### 2.2 Resend For An Already-Verified Account

Use an active account email:

```bash
curl -i \
  -H "Content-Type: application/json" \
  -d '{"email":"phase3user+02@example.com"}' \
  http://127.0.0.1:8000/v1/auth/resend-verification
```

Expected:

- `204 No Content`
- current implementation treats this as a safe no-op

---

## 3. Logout Invalidation Check

Before logout, copy the current session token value from `/tmp/rifthub-cookies.txt`.

Logout normally:

```bash
curl -i -b /tmp/rifthub-cookies.txt -c /tmp/rifthub-cookies.txt \
  -X POST \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  http://127.0.0.1:8000/v1/auth/logout
```

Expected:

- `204 No Content`

Then try the old session token directly:

```bash
curl -i -b "rifthub_session=<OLD_SESSION_VALUE>" \
  http://127.0.0.1:8000/v1/auth/me
```

Expected:

- `401 unauthenticated`

If needed, log back in afterward and refresh `CSRF_TOKEN`.

---

## 4. Login Enumeration Contract Check

### 4.1 Unknown Email

```bash
curl -i \
  -H "Content-Type: application/json" \
  -d '{"email":"doesnotexist@example.com","password":"anything"}' \
  http://127.0.0.1:8000/v1/auth/login
```

### 4.2 Known Email, Wrong Password

```bash
curl -i \
  -H "Content-Type: application/json" \
  -d '{"email":"phase3user+02@example.com","password":"wrong-password"}' \
  http://127.0.0.1:8000/v1/auth/login
```

Expected for both:

- `401`
- same `invalid_credentials` error contract

---

## 5. Unauthenticated Read Viewer Fields

Use any real post id.

```bash
curl -i http://127.0.0.1:8000/v1/feeds/top
curl -i http://127.0.0.1:8000/v1/posts/<POST_ID>
curl -i "http://127.0.0.1:8000/v1/posts/<POST_ID>/comments?sort=top"
```

Expected on unauthenticated responses:

- `viewer_vote = null`
- `viewer_can_edit = false`
- `viewer_can_moderate = false`

---

## 6. Comment Sort Spot Checks

```bash
curl -i "http://127.0.0.1:8000/v1/posts/<POST_ID>/comments?sort=new"
curl -i "http://127.0.0.1:8000/v1/posts/<POST_ID>/comments?sort=old"
```

Expected:

- both return `200 OK`
- ordering differs appropriately from `top`

---

## 7. Cross-Post Parent Injection Check

Use:

- `<POST_ID>` from post A
- `<COMMENT_ID_FROM_OTHER_POST>` from post B

```bash
curl -i -b /tmp/rifthub-cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  -d '{"body_markdown":"Injected reply","parent_comment_id":"<COMMENT_ID_FROM_OTHER_POST>"}' \
  http://127.0.0.1:8000/v1/posts/<POST_ID>/comments
```

Expected:

- non-success response
- current behavior: `404 comment_not_found`

---

## 8. Expired Job Feed Check

Create an expired job:

```bash
curl -i -b /tmp/rifthub-cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  -d '{"post_type":"job","category":"jobs","title":"Expired job","body_markdown":"Should not show in jobs feed","job_expires_at":"2020-01-01T00:00:00Z"}' \
  http://127.0.0.1:8000/v1/posts
```

Then:

```bash
curl -i http://127.0.0.1:8000/v1/feeds/jobs
```

Expected:

- expired job should not appear in jobs feed

---

## 9. Missing-Target Vote Check

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

## 10. Optional Pagination Spot Check

Only do this if you have enough posts to produce a cursor:

```bash
curl -i "http://127.0.0.1:8000/v1/feeds/top?limit=1"
curl -i "http://127.0.0.1:8000/v1/feeds/top?limit=1&cursor=<NEXT_CURSOR>"
```

Expected:

- second page works
- no duplicate item from page one

---

## Done

This delta checklist is complete when:

1. auth hardening checks behave as expected
2. logout invalidates the old session
3. resend-verification behaves safely
4. viewer fields stay neutral for unauthenticated reads
5. comment sort, missing-target vote, and cross-post parent checks behave correctly
6. expired jobs remain out of the jobs feed
