# API_SPEC.md

## Project
**Working name:** RiftHub  
**System type:** Community-ranked discussion and discovery platform for African tech

---

# 1. Purpose

This document defines the HTTP API contract for the platform.

The API is designed to support:

- authentication and user identity
- feed retrieval
- post submission and retrieval
- threaded comments
- voting
- moderation workflows
- ingestion administration
- admin and operator visibility into source pipelines

This specification is designed for a **FastAPI** backend and a **Next.js** frontend.

---

# 2. API Design Principles

## 2.1 Core principles

1. **REST-first**
   - The API uses REST conventions for clarity, debuggability, and speed of implementation.
   - GraphQL is unnecessary for v1.

2. **Stable resource modeling**
   - Top-level entities map cleanly to tables and service modules.
   - `posts`, `comments`, `users`, `feeds`, `flags`, and `sources` are first-class resources.

3. **Role-aware behavior**
   - Responses may include fields conditionally depending on authentication state and permissions.

4. **Schema-aligned**
   - Endpoints align closely with the `DATABASE_SCHEMA.md` model.
   - Business logic lives in service layers, not in route handlers.

5. **Future-safe**
   - The API supports future expansion such as moderator-only downvotes, bookmarks, and source analytics without requiring route redesign.

---

# 3. Base Conventions

## 3.1 Base URL

Example:

```text
https://api.thebeacon.africa
```

Versioning:

```text
/v1
```

Example full base:

```text
https://api.thebeacon.africa/v1
```

All endpoints below assume the `/v1` prefix.

## 3.2 Content type

Requests and responses use JSON unless otherwise specified.

```text
Content-Type: application/json
Accept: application/json
```

## 3.3 Authentication model

Recommended v1 approach:

- HTTP-only cookie session auth
- verification-first registration

Required cookie/session properties:

- `HttpOnly`
- `Secure`
- `SameSite=Lax` or `SameSite=Strict` where possible
- server-side validation of an opaque session token
- CSRF protection for state-changing requests using a session-bound double-submit token
- origin validation for browser-based mutating requests

Registration behavior for v1:

- `POST /auth/register` creates a pending account
- no authenticated session is issued until verification completes
- `POST /auth/verify` completes verification, creates the session, and sets the auth/CSRF cookies
- `POST /auth/resend-verification` rotates the active verification token for a pending account and retries delivery without authenticating the user

Because frontend and backend may be hosted separately (`Vercel` + `Railway`), cross-origin cookie behavior and CSRF defenses must be designed explicitly. The API spec below assumes browser clients authenticate with a session cookie.

Example:

```text
Cookie: beacon_session=<opaque-session-id>
X-CSRF-Token: <csrf-token>
```

## 3.4 ID format

All resource IDs are UUID strings.

Example:

```text
"id": "d290f1ee-6c54-4b01-90e6-d701748f0851"
```

## 3.5 Timestamp format

All timestamps are ISO 8601 UTC strings.

Example:

```text
"created_at": "2026-03-13T17:45:00Z"
```

# 4. Error Response Standard

All errors should use a consistent envelope.

## 4.1 Error shape

```JSON
{
  "error": {
    "code": "post_not_found",
    "message": "The requested post does not exist.",
    "details": null
  }
}
```

## 4.2 Fields

| Field     | Type           | Description                  |
| --------- | -------------- | ---------------------------- |
| `code`    | string         | machine-readable error code  |
| `message` | string         | human-readable explanation   |
| `details` | object or null | optional structured metadata |


## 4.3 Common HTTP status codes

| Status | Meaning              |
| ------ | -------------------- |
| `200`  | success              |
| `201`  | resource created     |
| `204`  | success, no body     |
| `400`  | invalid request      |
| `401`  | unauthenticated      |
| `403`  | unauthorized         |
| `404`  | resource not found   |
| `409`  | conflict / duplicate |
| `422`  | validation failure   |
| `429`  | rate limited         |
| `500`  | internal error       |


## 4.4 Common error codes

| Code                   | Meaning                       |
| ---------------------- | ----------------------------- |
| `unauthenticated`      | user is not logged in         |
| `forbidden`            | user lacks permission         |
| `validation_error`     | request body invalid          |
| `post_not_found`       | post does not exist           |
| `comment_not_found`    | comment does not exist        |
| `user_not_found`       | user does not exist           |
| `duplicate_submission` | normalized URL already exists |
| `vote_not_allowed`     | invalid vote action           |
| `rate_limited`         | rate limit exceeded           |
| `flag_not_found`       | flag does not exist           |
| `source_not_found`     | source does not exist         |
| `account_pending_verification` | account exists but is not yet verified |
| `verification_token_invalid` | verification token is invalid |
| `verification_token_expired` | verification token has expired |


# 5. Response Envelope Strategy

For consistency, collection endpoints should return metadata plus items.

## 5.1 Collection response shape

```JSON
{
  "items": [],
  "page_info": {
    "next_cursor": null,
    "has_next_page": false
  }
}
```

## 5.2 Single resource response shape

Single-resource endpoints may return the resource directly:

```JSON
{
  "post": {
    "id": "..."
  }
}
```

This keeps responses self-describing and easier to extend.


# 6. Shared Resource Shapes

## 6.1 User object

```JSON
{
  "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "username": "bheki",
  "bio": "Building for the African tech ecosystem.",
  "role": "user",
  "status": "active",
  "karma": 124,
  "post_count": 12,
  "comment_count": 47,
  "avatar_url": null,
  "created_at": "2026-03-01T10:00:00Z",
  "last_active_at": "2026-03-13T17:40:00Z"
}
```
- `email` should not be returned publicly
- `role` and `status` may be hidden or restricted in public contexts depending on policy

## 6.2 Domain object

```JSON
{
  "id": "f731ec9c-4d7c-4e2b-a6a8-17fbdc041122",
  "hostname": "techcabal.com",
  "display_name": "TechCabal",
  "trust_score": 1.0,
  "is_blocked": false
}
```

## 6.3 Post object

```JSON
{
  "id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
  "title": "African startups are rethinking logistics infrastructure",
  "slug": "african-startups-are-rethinking-logistics-infrastructure",
  "post_type": "link",
  "category": "ecosystem",
  "status": "active",
  "url": "https://example.com/story",
  "url_normalized": "https://example.com/story",
  "body_markdown": null,
  "author": {
    "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "username": "bheki"
  },
  "domain": {
    "id": "f731ec9c-4d7c-4e2b-a6a8-17fbdc041122",
    "hostname": "example.com",
    "display_name": "Example"
  },
  "is_ingested": false,
  "upvote_count": 18,
  "downvote_count": 0,
  "comment_count": 7,
  "score": 18,
  "rank_score": 5.9142,
  "viewer_vote": 1,
  "viewer_can_edit": false,
  "viewer_can_moderate": false,
  "submitted_at": "2026-03-13T14:00:00Z",
  "created_at": "2026-03-13T14:00:00Z",
  "updated_at": "2026-03-13T14:00:00Z",
  "last_commented_at": "2026-03-13T16:10:00Z",
  "job_expires_at": null
}
```

Notes:

- `viewer_vote is 1, -1, or null`
- for upvote-only UI, frontend only uses `1` or `null`
- `viewer_can_edit` and `viewer_can_moderate` are convenience fields


## 6.4 Comment object

```JSON
{
  "id": "64b59dd8-9bf2-42f9-a0aa-51323cfab014",
  "post_id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
  "parent_comment_id": null,
  "depth": 0,
  "body_markdown": "This is one of the more interesting logistics pivots I have seen recently.",
  "status": "active",
  "author": {
    "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "username": "bheki"
  },
  "upvote_count": 5,
  "downvote_count": 0,
  "score": 5,
  "rank_score": 2.12,
  "viewer_vote": null,
  "viewer_can_edit": true,
  "viewer_can_moderate": false,
  "created_at": "2026-03-13T15:00:00Z",
  "updated_at": "2026-03-13T15:10:00Z"
}
```

## 6.5 Flag object

```JSON
{
  "id": "3cde12f0-7e7d-4f9e-8f84-394d5c38e4e7",
  "target_type": "post",
  "target_id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
  "reason_code": "spam",
  "notes": "Looks promotional and duplicated.",
  "status": "open",
  "reporter_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "reviewed_by_user_id": null,
  "reviewed_at": null,
  "created_at": "2026-03-13T16:30:00Z"
}
```

`reason_code` must use the enum-backed moderation reasons:

- `spam`
- `abuse`
- `misinformation`
- `off_topic`
- `other`

## 6.6 Source object

```JSON
{
  "id": "edbb1b6d-6f63-4b4a-8b1b-47eb0b8b4c29",
  "name": "TechCabal RSS",
  "source_type": "rss",
  "status": "active",
  "url": "https://example.com/rss.xml",
  "site_url": "https://example.com",
  "default_category": "ecosystem",
  "trust_score": 1.0,
  "auto_publish": true,
  "poll_interval_minutes": 30,
  "last_checked_at": "2026-03-13T17:15:00Z",
  "last_success_at": "2026-03-13T17:15:00Z",
  "last_error_at": null,
  "last_error_message": null,
  "created_at": "2026-03-01T10:00:00Z",
  "updated_at": "2026-03-13T17:15:00Z"
}
```

# 7. Pagination Standard

Cursor pagination should be used on feed-like resources.

## 7.1 Request parameters

| Parameter | Type    | Description              |
| --------- | ------- | ------------------------ |
| `limit`   | integer | page size                |
| `cursor`  | string  | opaque pagination cursor |


## 7.2 Response format

```JSON
{
  "items": [],
  "page_info": {
    "next_cursor": "opaque_cursor_string",
    "has_next_page": true
  }
}
```

## 7.3 Defaults

- default `limit`: `30`
- max `limit`: `100`


# 8. Authentication Endpoints

## 8.1 Register

**Endpoint**

```http
POST /auth/register
```

**Purpose**

Create a new pending user account.

**Request body**

```JSON
{
  "username": "bheki",
  "email": "b@example.com",
  "password": "strong-password-here"
}
```


**Validation rules**

- `username`: 3–32 chars, lowercase canonical storage, `[a-z0-9_]+`
- `email`: valid email format
- `password`: minimum to maximum strength policy enforced

**Success response**

**201 Created**

```JSON
{
  "verification_required": true,
  "user": {
    "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "username": "bheki",
    "bio": null,
    "role": "user",
    "status": "pending",
    "karma": 0,
    "post_count": 0,
    "comment_count": 0,
    "avatar_url": null,
    "created_at": "2026-03-13T18:00:00Z",
    "last_active_at": "2026-03-13T18:00:00Z"
  }
}
```

The server does **not** set an authenticated session cookie on register. Verification must complete first.

**Failure cases**

- `409 duplicate username`
- `409 duplicate email`
- `422 invalid username/email/password`

## 8.2 Verify

**Endpoint**

```http
POST /auth/verify
```

**Purpose**

Complete account verification and start the authenticated session.

**Request body**

```JSON
{
  "token": "opaque-verification-token"
}
```

**Success response**

**200 OK**

```JSON
{
  "user": {
    "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "username": "bheki",
    "bio": null,
    "role": "user",
    "status": "active",
    "karma": 0,
    "post_count": 0,
    "comment_count": 0,
    "avatar_url": null,
    "created_at": "2026-03-13T18:00:00Z",
    "last_active_at": "2026-03-13T18:05:00Z"
  }
}
```

The server should set the authenticated session cookie and CSRF cookie on successful verification.

**Failure cases**

- `400 verification_token_invalid`
- `400 verification_token_expired`
- `409 account already verified`

## 8.3 Resend verification

**Endpoint**

```http
POST /auth/resend-verification
```

**Purpose**

Rotate the active verification token for a pending account and attempt delivery again.

**Request body**

```JSON
{
  "email": "b@example.com"
}
```

**Success response**

**204 No Content**

Rules:

- the server does not authenticate the user
- the server does not set auth or CSRF cookies
- if a matching pending account exists, prior unconsumed verification token(s) are invalidated and a new one is issued
- if the account does not exist or is no longer pending, the endpoint still returns `204`

**Failure cases**

- `422 invalid email`
- `429 rate limited`

# 8.4 Login

**Endpoint**

```http
POST /auth/login
```

**Request body**

```JSON
{
  "email": "b@example.com",
  "password": "strong-password-here"
}
```

**Success response**

**200 OK**

```JSON
{
  "user": {
    "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "username": "bheki",
    "bio": null,
    "role": "user",
    "status": "active",
    "karma": 0,
    "post_count": 0,
    "comment_count": 0,
    "avatar_url": null,
    "created_at": "2026-03-13T18:00:00Z",
    "last_active_at": "2026-03-13T18:05:00Z"
  }
}
```

The server should set the session cookie with `Set-Cookie` on successful login. No Bearer token payload is returned in v1.

**Failure cases**

- `401 invalid credentials`
- `403 account_pending_verification`
- `403 account suspended or banned`


## 8.5 Logout

**Endpoint**

```http
POST /auth/logout
```

**Success response**

**204 No Content**

The server should invalidate the current session server-side if present, clear the session cookie, clear the CSRF cookie, and still return `204` even when no valid session exists.

## 8.6 Current session

**Endpoint**

```http
GET /auth/me
```

**Purpose**

Return current authenticated user.

**Success response**

**200 OK**

```JSON
{
  "user": {
    "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "username": "bheki",
    "bio": "Building for the African tech ecosystem.",
    "role": "user",
    "status": "active",
    "karma": 124,
    "post_count": 12,
    "comment_count": 47,
    "avatar_url": null,
    "created_at": "2026-03-01T10:00:00Z",
    "last_active_at": "2026-03-13T17:40:00Z"
  }
}
```

**Failure cases**

**401 unauthenticated**

If the request is authenticated but the CSRF cookie is missing, the server may refresh the CSRF cookie in the response.


# 9. User Endpoints

## 9.1 Get public user profile

**Endpoint**

```http
GET /users/{username}
```

**Success response**

**200 OK**

```JSON
{
  "user": {
    "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "username": "bheki",
    "bio": "Building for the African tech ecosystem.",
    "role": "user",
    "status": "active",
    "karma": 124,
    "post_count": 12,
    "comment_count": 47,
    "avatar_url": null,
    "created_at": "2026-03-01T10:00:00Z",
    "last_active_at": "2026-03-13T17:40:00Z"
  }
}
```

**Failure cases**

- `404 user_not_found`

## 9.2 Get user posts

**Endpoint**

```http
GET /users/{username}/posts
```

**Query params**

- limit
- cursor

**Success response**

**200 OK**

```json
{
  "items": [
    {
      "id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
      "title": "African startups are rethinking logistics infrastructure",
      "slug": "african-startups-are-rethinking-logistics-infrastructure",
      "post_type": "link",
      "category": "ecosystem",
      "status": "active",
      "url": "https://example.com/story",
      "body_markdown": null,
      "author": {
        "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
        "username": "bheki"
      },
      "domain": {
        "id": "f731ec9c-4d7c-4e2b-a6a8-17fbdc041122",
        "hostname": "example.com",
        "display_name": "Example"
      },
      "is_ingested": false,
      "upvote_count": 18,
      "downvote_count": 0,
      "comment_count": 7,
      "score": 18,
      "rank_score": 5.9142,
      "viewer_vote": null,
      "viewer_can_edit": false,
      "viewer_can_moderate": false,
      "submitted_at": "2026-03-13T14:00:00Z",
      "created_at": "2026-03-13T14:00:00Z",
      "updated_at": "2026-03-13T14:00:00Z",
      "last_commented_at": "2026-03-13T16:10:00Z",
      "job_expires_at": null
    }
  ],
  "page_info": {
    "next_cursor": null,
    "has_next_page": false
  }
}
```

## 9.3 Get user comments

**Endpoint**

```http
GET /users/{username}/comments
```

**Query params**

- limit
- cursor

**Success response**

**200 OK**

```JSON
{
  "items": [
    {
      "id": "64b59dd8-9bf2-42f9-a0aa-51323cfab014",
      "post_id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
      "parent_comment_id": null,
      "depth": 0,
      "body_markdown": "This is one of the more interesting logistics pivots I have seen recently.",
      "status": "active",
      "author": {
        "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
        "username": "bheki"
      },
      "upvote_count": 5,
      "downvote_count": 0,
      "score": 5,
      "rank_score": 2.12,
      "viewer_vote": null,
      "viewer_can_edit": false,
      "viewer_can_moderate": false,
      "created_at": "2026-03-13T15:00:00Z",
      "updated_at": "2026-03-13T15:10:00Z"
    }
  ],
  "page_info": {
    "next_cursor": null,
    "has_next_page": false
  }
}
```

# 10. Feed Endpoints

## 10.1 Get top feed

**Endpoint**

```http
GET /feeds/top
```

**Query params**

| Param    | Type    | Notes               |
| -------- | ------- | ------------------- |
| `limit`  | integer | default 30, max 100 |
| `cursor` | string  | pagination cursor   |

**Success response**

**200 OK**

```JSON
{
  "items": [
    {
      "id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
      "title": "African startups are rethinking logistics infrastructure",
      "slug": "african-startups-are-rethinking-logistics-infrastructure",
      "post_type": "link",
      "category": "ecosystem",
      "status": "active",
      "url": "https://example.com/story",
      "body_markdown": null,
      "author": {
        "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
        "username": "bheki"
      },
      "domain": {
        "id": "f731ec9c-4d7c-4e2b-a6a8-17fbdc041122",
        "hostname": "example.com",
        "display_name": "Example"
      },
      "is_ingested": false,
      "upvote_count": 18,
      "downvote_count": 0,
      "comment_count": 7,
      "score": 18,
      "rank_score": 5.9142,
      "viewer_vote": null,
      "viewer_can_edit": false,
      "viewer_can_moderate": false,
      "submitted_at": "2026-03-13T14:00:00Z",
      "created_at": "2026-03-13T14:00:00Z",
      "updated_at": "2026-03-13T14:00:00Z",
      "last_commented_at": "2026-03-13T16:10:00Z",
      "job_expires_at": null
    }
  ],
  "page_info": {
    "next_cursor": "opaque_cursor_string",
    "has_next_page": true
  }
}
```


## 10.2 Get new feed

**Endpoint**

```http
GET /feeds/new
```

**Notes**


- Returns active posts ordered by `submitted_at desc`.
- Response shape is identical to `/feeds/top`.

## 10.3 Get ask feed

**Endpoint**

```http
GET /feeds/ask
```

**Notes**

- Returns posts where `category = ask`, usually text posts.
- Response shape is identical to `/feeds/top`.

## 10.4 Get show feed

**Endpoint**

```http
GET /feeds/show
```

**Notes**

- Returns posts where `category = show`.
- Response shape is identical to `/feeds/top`.

## 10.5 Get jobs feed

**Endpoint**

```http
GET /feeds/jobs
```

**Notes**

- Returns posts where `post_type = job`.
- Jobs should be filtered to rows where `job_expires_at` is `null` or in the future.
- Response shape is identical to `/feeds/top`.

## 10.6 Optional category feed

**Endpoint**

```http
GET /feeds/category/{category}
```

**Notes**

- This endpoint is optional but useful if category-specific views expand beyond the main tabs.
- Valid categories must align with `category_enum`.

# 11. Post Endpoints

## 11.1 Create post

**Endpoint**

```http
POST /posts
```

**Auth**

Required.

**Request body for link post**

```JSON
{
  "post_type": "link",
  "category": "ecosystem",
  "title": "African startups are rethinking logistics infrastructure",
  "url": "https://example.com/story"
}
```

**Request body for text post**

```JSON
{
  "post_type": "text",
  "category": "ask",
  "title": "What are the best ways to distribute African tech content today?",
  "body_markdown": "I am curious what channels founders still trust."
}
```

**Request body for job post**

```JSON
{
  "post_type": "job",
  "category": "jobs",
  "title": "Senior Backend Engineer at Example Startup",
  "url": "https://example.com/jobs/backend",
  "body_markdown": "Remote-friendly. Python and Postgres experience preferred.",
  "job_expires_at": "2026-04-13T00:00:00Z"
}
```

**Validation rules**

- `title` is required.
- `post_type` is required.
- `category` is required.
- `link` posts require `url`.
- `text` posts require `body_markdown`.
- `job` posts require at least `url` or `body_markdown`.

**Success response**

**201 Created**

```JSON
{
  "post": {
    "id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
    "title": "African startups are rethinking logistics infrastructure",
    "slug": "african-startups-are-rethinking-logistics-infrastructure",
    "post_type": "link",
    "category": "ecosystem",
    "status": "active",
    "url": "https://example.com/story",
    "url_normalized": "https://example.com/story",
    "body_markdown": null,
    "author": {
      "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
      "username": "bheki"
    },
    "domain": {
      "id": "f731ec9c-4d7c-4e2b-a6a8-17fbdc041122",
      "hostname": "example.com",
      "display_name": "Example"
    },
    "is_ingested": false,
    "upvote_count": 0,
    "downvote_count": 0,
    "comment_count": 0,
    "score": 0,
    "rank_score": 0.0,
    "viewer_vote": null,
    "viewer_can_edit": true,
    "viewer_can_moderate": false,
    "submitted_at": "2026-03-13T18:20:00Z",
    "created_at": "2026-03-13T18:20:00Z",
    "updated_at": "2026-03-13T18:20:00Z",
    "last_commented_at": null,
    "job_expires_at": null
  }
}
```

**Failure cases**

- `401` `unauthenticated`
- `409` `duplicate_submission`
- `422` `validation_error`

**Duplicate submission behavior**

If a normalized URL already exists within repost window policy, the recommended response is:

**409 Conflict**

```JSON
{
  "error": {
    "code": "duplicate_submission",
    "message": "This story has already been submitted recently.",
    "details": {
      "existing_post_id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
      "existing_post_slug": "african-startups-are-rethinking-logistics-infrastructure"
    }
  }
}
```

## 11.2 Get post by ID

**Endpoint**

```http
GET /posts/{post_id}
```

**Success response**

**200 OK**

```JSON
{
  "post": {
    "id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
    "title": "African startups are rethinking logistics infrastructure",
    "slug": "african-startups-are-rethinking-logistics-infrastructure",
    "post_type": "link",
    "category": "ecosystem",
    "status": "active",
    "url": "https://example.com/story",
    "url_normalized": "https://example.com/story",
    "body_markdown": null,
    "author": {
      "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
      "username": "bheki"
    },
    "domain": {
      "id": "f731ec9c-4d7c-4e2b-a6a8-17fbdc041122",
      "hostname": "example.com",
      "display_name": "Example"
    },
    "is_ingested": false,
    "upvote_count": 18,
    "downvote_count": 0,
    "comment_count": 7,
    "score": 18,
    "rank_score": 5.9142,
    "viewer_vote": 1,
    "viewer_can_edit": false,
    "viewer_can_moderate": false,
    "submitted_at": "2026-03-13T14:00:00Z",
    "created_at": "2026-03-13T14:00:00Z",
    "updated_at": "2026-03-13T14:00:00Z",
    "last_commented_at": "2026-03-13T16:10:00Z",
    "job_expires_at": null
  }
}
```

## 11.3 Get post by ID and slug

**Endpoint**

```http
GET /posts/{post_id}/{slug}
```

**Notes**

This is optional at the API level if the frontend resolves by ID only, but it is useful for canonical routing and slug validation.

**Behavior options**

- Return the resource directly even if the slug mismatches.
- Return the canonical slug in the response and let the frontend redirect.

Recommended behavior: accept the slug, resolve by ID, and include the canonical slug in the response.

## 11.4 Update post

**Endpoint**

```http
PATCH /posts/{post_id}
```

**Auth**

Required.

**Permissions**

Allowed for:

- post author within the edit window
- moderator or admin beyond the author window where policy allows

**Request body example**

```JSON
{
  "title": "Updated title for the post",
  "body_markdown": "Updated body content"
}
```

**Editable fields**

- `title`
- `body_markdown`
- `category`, but only if moderation or admin policy allows it
- `job_expires_at` for job posts if policy allows

Do not allow arbitrary URL mutation for published link posts in v1 unless there is a clear moderation or admin workflow.

**Success response**

**200 OK**

```JSON
{
  "post": {
    "id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
    "title": "Updated title for the post",
    "slug": "updated-title-for-the-post",
    "post_type": "text",
    "category": "ask",
    "status": "active",
    "url": null,
    "url_normalized": null,
    "body_markdown": "Updated body content",
    "author": {
      "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
      "username": "bheki"
    },
    "domain": null,
    "is_ingested": false,
    "upvote_count": 4,
    "downvote_count": 0,
    "comment_count": 3,
    "score": 4,
    "rank_score": 1.874,
    "viewer_vote": null,
    "viewer_can_edit": true,
    "viewer_can_moderate": false,
    "submitted_at": "2026-03-13T15:00:00Z",
    "created_at": "2026-03-13T15:00:00Z",
    "updated_at": "2026-03-13T15:10:00Z",
    "last_commented_at": "2026-03-13T15:09:00Z",
    "job_expires_at": null
  }
}
```

**Failure cases**

- `401` `unauthenticated`
- `403` `forbidden`
- `404` `post_not_found`
- `422` `validation_error`

## 11.5 Remove post

**Endpoint**

```http
DELETE /posts/{post_id}
```

**Auth**

Required.

**Notes**

This is effectively a soft-delete endpoint. It should transition `status` rather than hard-delete the row.

Possible behaviors:

- author removes own post within allowed policy
- moderator removes any post
- returned resource may later render as removed

**Success response**

**200 OK**

```JSON
{
  "post": {
    "id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
    "status": "removed"
  }
}
```

Alternative acceptable response:

**204 No Content**

# 12. Comment Endpoints

## 12.1 Create comment

**Endpoint**

```http
POST /posts/{post_id}/comments
```

**Auth**

Required.

**Request body for top-level comment**

```JSON
{
  "body_markdown": "This is a strong example of ecosystem infrastructure."
}
```

**Request body for reply**

```JSON
{
  "body_markdown": "I agree. Distribution is the actual moat here.",
  "parent_comment_id": "64b59dd8-9bf2-42f9-a0aa-51323cfab014"
}
```

**Validation rules**

- `body_markdown` is required.
- `parent_comment_id` must belong to the same post.
- Nesting depth cannot exceed the configured policy maximum.

**Success response**

**201 Created**

```JSON
{
  "comment": {
    "id": "64b59dd8-9bf2-42f9-a0aa-51323cfab014",
    "post_id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
    "parent_comment_id": null,
    "depth": 0,
    "body_markdown": "This is a strong example of ecosystem infrastructure.",
    "status": "active",
    "author": {
      "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
      "username": "bheki"
    },
    "upvote_count": 0,
    "downvote_count": 0,
    "score": 0,
    "rank_score": 0.0,
    "viewer_vote": null,
    "viewer_can_edit": true,
    "viewer_can_moderate": false,
    "created_at": "2026-03-13T18:30:00Z",
    "updated_at": "2026-03-13T18:30:00Z"
  }
}
```

## 12.2 Get comments for post

**Endpoint**

```http
GET /posts/{post_id}/comments
```

**Query params**

| Param  | Type   | Notes                     |
| ------ | ------ | ------------------------- |
| `sort` | string | optional: `top`, `new`, `old` |

**Success response**

**200 OK**

```JSON
{
  "items": [
    {
      "id": "64b59dd8-9bf2-42f9-a0aa-51323cfab014",
      "post_id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
      "parent_comment_id": null,
      "depth": 0,
      "body_markdown": "This is one of the more interesting logistics pivots I have seen recently.",
      "status": "active",
      "author": {
        "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
        "username": "bheki"
      },
      "upvote_count": 5,
      "downvote_count": 0,
      "score": 5,
      "rank_score": 2.12,
      "viewer_vote": null,
      "viewer_can_edit": false,
      "viewer_can_moderate": false,
      "created_at": "2026-03-13T15:00:00Z",
      "updated_at": "2026-03-13T15:10:00Z"
    },
    {
      "id": "aa0daec2-d8d3-4671-a49d-5880d3a9c8b3",
      "post_id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
      "parent_comment_id": "64b59dd8-9bf2-42f9-a0aa-51323cfab014",
      "depth": 1,
      "body_markdown": "The regional angle is what makes it different.",
      "status": "active",
      "author": {
        "id": "f062f631-5a91-4d22-a6e5-5a80c5e16b1d",
        "username": "sam"
      },
      "upvote_count": 2,
      "downvote_count": 0,
      "score": 2,
      "rank_score": 0.88,
      "viewer_vote": null,
      "viewer_can_edit": false,
      "viewer_can_moderate": false,
      "created_at": "2026-03-13T15:20:00Z",
      "updated_at": "2026-03-13T15:20:00Z"
    }
  ]
}
```

**Notes**

- A flat list with `parent_comment_id` and `depth` is easier for API payloads.
- The frontend reconstructs the thread tree.
- A nested response is possible later, but a flat response is simpler and more cacheable.

## 12.3 Update comment

**Endpoint**

```http
PATCH /comments/{comment_id}
```

**Auth**

Required.

**Permissions**

Allowed for:

- comment author within the edit window
- moderators or admins according to policy

**Request body**

```JSON
{
  "body_markdown": "Updated comment body."
}
```

**Success response**

**200 OK**

```JSON
{
  "comment": {
    "id": "64b59dd8-9bf2-42f9-a0aa-51323cfab014",
    "post_id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
    "parent_comment_id": null,
    "depth": 0,
    "body_markdown": "Updated comment body.",
    "status": "active",
    "author": {
      "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
      "username": "bheki"
    },
    "upvote_count": 5,
    "downvote_count": 0,
    "score": 5,
    "rank_score": 2.12,
    "viewer_vote": null,
    "viewer_can_edit": true,
    "viewer_can_moderate": false,
    "created_at": "2026-03-13T15:00:00Z",
    "updated_at": "2026-03-13T15:25:00Z"
  }
}
```

## 12.4 Remove comment

**Endpoint**

```http
DELETE /comments/{comment_id}
```

**Auth**

Required.

**Notes**

Soft deletion is preferred. Child comments remain attached to preserve thread integrity.

**Success response**

**200 OK**

```JSON
{
  "comment": {
    "id": "64b59dd8-9bf2-42f9-a0aa-51323cfab014",
    "status": "removed"
  }
}
```

# 13. Voting Endpoints

Recommended v1 behavior: the UI exposes upvotes only, but payloads remain compatible with future downvotes.

## 13.1 Vote on post

**Endpoint**

```http
POST /posts/{post_id}/vote
```

**Auth**

Required.

**Request body**

Upvote-only UI payload:

```JSON
{
  "vote_value": 1
}
```

Future-compatible payload:

```JSON
{
  "vote_value": -1
}
```

**Success response**

**200 OK**

```JSON
{
  "post": {
    "id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
    "upvote_count": 19,
    "downvote_count": 0,
    "score": 19,
    "rank_score": 6.0142,
    "viewer_vote": 1
  }
}
```

**Failure cases**

- `401` `unauthenticated`
- `403` `vote_not_allowed`
- `404` `post_not_found`
- `422` `validation_error`

## 13.2 Remove vote from post

**Endpoint**

```http
DELETE /posts/{post_id}/vote
```

**Auth**

Required.

**Success response**

**200 OK**

```JSON
{
  "post": {
    "id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
    "upvote_count": 18,
    "downvote_count": 0,
    "score": 18,
    "rank_score": 5.9142,
    "viewer_vote": null
  }
}
```

## 13.3 Vote on comment

**Endpoint**

```http
POST /comments/{comment_id}/vote
```

**Auth**

Required.

**Request body**

```JSON
{
  "vote_value": 1
}
```

**Success response**

**200 OK**

```JSON
{
  "comment": {
    "id": "64b59dd8-9bf2-42f9-a0aa-51323cfab014",
    "upvote_count": 6,
    "downvote_count": 0,
    "score": 6,
    "rank_score": 2.31,
    "viewer_vote": 1
  }
}
```

## 13.4 Remove vote from comment

**Endpoint**

```http
DELETE /comments/{comment_id}/vote
```

**Auth**

Required.

**Success response**

**200 OK**

```JSON
{
  "comment": {
    "id": "64b59dd8-9bf2-42f9-a0aa-51323cfab014",
    "upvote_count": 5,
    "downvote_count": 0,
    "score": 5,
    "rank_score": 2.12,
    "viewer_vote": null
  }
}
```

# 14. Flagging Endpoints

## 14.1 Create flag

**Endpoint**

```http
POST /flags
```

**Auth**

Required.

**Request body**

```JSON
{
  "target_type": "post",
  "target_id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
  "reason_code": "spam",
  "notes": "Looks promotional and duplicated."
}
```

**Success response**

**201 Created**

```JSON
{
  "flag": {
    "id": "3cde12f0-7e7d-4f9e-8f84-394d5c38e4e7",
    "target_type": "post",
    "target_id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
    "reason_code": "spam",
    "notes": "Looks promotional and duplicated.",
    "status": "open",
    "reporter_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "reviewed_by_user_id": null,
    "reviewed_at": null,
    "created_at": "2026-03-13T18:45:00Z"
  }
}
```

**Failure cases**

- `401` `unauthenticated`
- `409` `duplicate_open_flag`
- `422` `validation_error`

# 15. Moderator Endpoints

All endpoints in this section require `moderator` or `admin` role.

## 15.1 Get open flags

**Endpoint**

```http
GET /moderation/flags
```

**Query params**

| Param    | Type    | Notes              |
| -------- | ------- | ------------------ |
| `status` | string  | default `open`     |
| `limit`  | integer | pagination         |
| `cursor` | string  | pagination cursor  |

**Success response**

**200 OK**

```JSON
{
  "items": [
    {
      "id": "3cde12f0-7e7d-4f9e-8f84-394d5c38e4e7",
      "target_type": "post",
      "target_id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
      "reason_code": "spam",
      "notes": "Looks promotional and duplicated.",
      "status": "open",
      "reporter_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
      "reviewed_by_user_id": null,
      "reviewed_at": null,
      "created_at": "2026-03-13T18:45:00Z"
    }
  ],
  "page_info": {
    "next_cursor": null,
    "has_next_page": false
  }
}
```

## 15.2 Hide post

**Endpoint**

```http
POST /moderation/posts/{post_id}/hide
```

**Request body**

```JSON
{
  "reason": "Spam / low-quality promotional content"
}
```

**Success response**

```JSON
{
  "post": {
    "id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
    "status": "hidden"
  }
}
```

## 15.3 Remove post

**Endpoint**

```http
POST /moderation/posts/{post_id}/remove
```

**Request body**

```JSON
{
  "reason": "Policy violation"
}
```

**Success response**

```JSON
{
  "post": {
    "id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
    "status": "removed"
  }
}
```

## 15.4 Lock post

**Endpoint**

```http
POST /moderation/posts/{post_id}/lock
```

**Request body**

```JSON
{
  "reason": "Thread derailed and requires closure"
}
```

**Success response**

```JSON
{
  "post": {
    "id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
    "status": "locked"
  }
}
```

## 15.5 Hide comment

**Endpoint**

```http
POST /moderation/comments/{comment_id}/hide
```

**Request body**

```JSON
{
  "reason": "Abusive language"
}
```

**Success response**

```JSON
{
  "comment": {
    "id": "64b59dd8-9bf2-42f9-a0aa-51323cfab014",
    "status": "hidden"
  }
}
```

## 15.6 Remove comment

**Endpoint**

```http
POST /moderation/comments/{comment_id}/remove
```

**Request body**

```JSON
{
  "reason": "Policy violation"
}
```

**Success response**

```JSON
{
  "comment": {
    "id": "64b59dd8-9bf2-42f9-a0aa-51323cfab014",
    "status": "removed"
  }
}
```

## 15.7 Suspend user

**Endpoint**

```http
POST /moderation/users/{user_id}/suspend
```

**Request body**

```JSON
{
  "reason": "Repeated spam submissions"
}
```

**Success response**

```JSON
{
  "user": {
    "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "status": "suspended"
  }
}
```

## 15.8 Ban user

**Endpoint**

```http
POST /moderation/users/{user_id}/ban
```

**Request body**

```JSON
{
  "reason": "Severe repeated abuse"
}
```

**Success response**

```JSON
{
  "user": {
    "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "status": "banned"
  }
}
```

## 15.9 Reclassify post category

**Endpoint**

```http
POST /moderation/posts/{post_id}/reclassify
```

**Request body**

```JSON
{
  "category": "funding",
  "reason": "Wrong category selected by submitter"
}
```

**Success response**

```JSON
{
  "post": {
    "id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d",
    "category": "funding"
  }
}
```

# 16. Source / Ingestion Admin Endpoints

All endpoints in this section require moderator or admin privileges. In a small v1 team, admin-only access is also acceptable.

## 16.1 Get sources

**Endpoint**

```http
GET /admin/sources
```

**Query params**

| Param    | Type    | Notes             |
| -------- | ------- | ----------------- |
| `status` | string  | optional filter   |
| `limit`  | integer | pagination        |
| `cursor` | string  | pagination cursor |

**Success response**

```JSON
{
  "items": [
    {
      "id": "edbb1b6d-6f63-4b4a-8b1b-47eb0b8b4c29",
      "name": "TechCabal RSS",
      "source_type": "rss",
      "status": "active",
      "url": "https://example.com/rss.xml",
      "site_url": "https://example.com",
      "default_category": "ecosystem",
      "trust_score": 1.0,
      "auto_publish": true,
      "poll_interval_minutes": 30,
      "last_checked_at": "2026-03-13T17:15:00Z",
      "last_success_at": "2026-03-13T17:15:00Z",
      "last_error_at": null,
      "last_error_message": null,
      "created_at": "2026-03-01T10:00:00Z",
      "updated_at": "2026-03-13T17:15:00Z"
    }
  ],
  "page_info": {
    "next_cursor": null,
    "has_next_page": false
  }
}
```

## 16.2 Create source

**Endpoint**

```http
POST /admin/sources
```

**Request body**

```JSON
{
  "name": "TechCabal RSS",
  "source_type": "rss",
  "url": "https://example.com/rss.xml",
  "site_url": "https://example.com",
  "default_category": "ecosystem",
  "trust_score": 1.0,
  "auto_publish": true,
  "poll_interval_minutes": 30
}
```

**Success response**

**201 Created**

```JSON
{
  "source": {
    "id": "edbb1b6d-6f63-4b4a-8b1b-47eb0b8b4c29",
    "name": "TechCabal RSS",
    "source_type": "rss",
    "status": "active",
    "url": "https://example.com/rss.xml",
    "site_url": "https://example.com",
    "default_category": "ecosystem",
    "trust_score": 1.0,
    "auto_publish": true,
    "poll_interval_minutes": 30,
    "last_checked_at": null,
    "last_success_at": null,
    "last_error_at": null,
    "last_error_message": null,
    "created_at": "2026-03-13T18:50:00Z",
    "updated_at": "2026-03-13T18:50:00Z"
  }
}
```

## 16.3 Update source

**Endpoint**

```http
PATCH /admin/sources/{source_id}
```

**Request body example**

```JSON
{
  "status": "paused",
  "auto_publish": false,
  "poll_interval_minutes": 60
}
```

**Success response**

```JSON
{
  "source": {
    "id": "edbb1b6d-6f63-4b4a-8b1b-47eb0b8b4c29",
    "name": "TechCabal RSS",
    "source_type": "rss",
    "status": "paused",
    "url": "https://example.com/rss.xml",
    "site_url": "https://example.com",
    "default_category": "ecosystem",
    "trust_score": 1.0,
    "auto_publish": false,
    "poll_interval_minutes": 60,
    "last_checked_at": "2026-03-13T17:15:00Z",
    "last_success_at": "2026-03-13T17:15:00Z",
    "last_error_at": null,
    "last_error_message": null,
    "created_at": "2026-03-01T10:00:00Z",
    "updated_at": "2026-03-13T18:55:00Z"
  }
}
```

## 16.4 Get ingestion items

**Endpoint**

```http
GET /admin/ingestion/items
```

**Query params**

| Param      | Type    | Notes                      |
| ---------- | ------- | -------------------------- |
| `status`   | string  | filter by ingestion status |
| `source_id` | UUID    | optional source filter     |
| `limit`    | integer | pagination                 |
| `cursor`   | string  | pagination cursor          |

**Success response**

```JSON
{
  "items": [
    {
      "id": "4ac0f708-c4cb-4fe3-92d1-4e93b6cf894a",
      "source_id": "edbb1b6d-6f63-4b4a-8b1b-47eb0b8b4c29",
      "external_id": "rss-entry-123",
      "title": "New fintech policies are reshaping startup compliance",
      "url": "https://example.com/story",
      "url_normalized": "https://example.com/story",
      "published_at_external": "2026-03-13T12:00:00Z",
      "discovered_at": "2026-03-13T12:03:00Z",
      "ingestion_status": "awaiting_review",
      "detected_category": "policy",
      "linked_post_id": null,
      "dedupe_match_post_id": null,
      "processing_notes": null,
      "created_at": "2026-03-13T12:03:00Z",
      "updated_at": "2026-03-13T12:03:00Z"
    }
  ],
  "page_info": {
    "next_cursor": null,
    "has_next_page": false
  }
}
```

`ingestion_status` should use the persisted lifecycle documented in the schema and ingestion docs:

- `discovered`
- `normalized`
- `duplicate`
- `classified`
- `awaiting_review`
- `published`
- `rejected`
- `failed`

## 16.5 Trigger ingestion run

**Endpoint**

```http
POST /admin/ingestion/run
```

**Request body**

Optional body:

```JSON
{
  "source_id": "edbb1b6d-6f63-4b4a-8b1b-47eb0b8b4c29"
}
```

If omitted, the system may trigger all due active sources.

**Success response**

```JSON
{
  "status": "accepted",
  "message": "Ingestion run accepted."
}
```

## 16.6 Approve ingestion item

**Endpoint**

```http
POST /admin/ingestion/items/{item_id}/approve
```

**Request body example**

```JSON
{
  "category": "policy"
}
```

**Success response**

```JSON
{
  "ingestion_item": {
    "id": "4ac0f708-c4cb-4fe3-92d1-4e93b6cf894a",
    "ingestion_status": "published",
    "linked_post_id": "58d4df53-f1c8-41d2-bf75-8f27d8c6f91d"
  }
}
```

## 16.7 Reject ingestion item

**Endpoint**

```http
POST /admin/ingestion/items/{item_id}/reject
```

**Request body**

```JSON
{
  "reason": "Duplicate or low relevance"
}
```

**Success response**

```JSON
{
  "ingestion_item": {
    "id": "4ac0f708-c4cb-4fe3-92d1-4e93b6cf894a",
    "ingestion_status": "rejected"
  }
}
```

# 17. Rate Limiting Recommendations

These are not route contracts, but they matter operationally.

## 17.1 Suggested initial limits

| Route group          | Suggested limit              |
| -------------------- | ---------------------------- |
| `login`              | strict per IP and account    |
| `register`           | strict per IP                |
| `create post`        | per user per day             |
| `create comment`     | per user per minute          |
| `votes`              | per user per minute burst protection |
| `flags`              | per user per hour            |
| `moderation actions` | moderate protection          |
| `ingestion run`      | admin-only, strict           |

**Example response**

**429 Too Many Requests**

```JSON
{
  "error": {
    "code": "rate_limited",
    "message": "Too many requests. Please try again later.",
    "details": null
  }
}
```

# 18. Authorization Matrix

| Endpoint Group              | Guest | User | Moderator | Admin |
| --------------------------- | ----- | ---- | --------- | ----- |
| View feeds                  | yes   | yes  | yes       | yes   |
| View posts and comments     | yes   | yes  | yes       | yes   |
| Register and login          | yes   | yes  | yes       | yes   |
| Create post                 | no    | yes  | yes       | yes   |
| Comment                     | no    | yes  | yes       | yes   |
| Vote                        | no    | yes  | yes       | yes   |
| Flag                        | no    | yes  | yes       | yes   |
| View public user profiles   | yes   | yes  | yes       | yes   |
| View open flags             | no    | no   | yes       | yes   |
| Moderate posts and comments | no    | no   | yes       | yes   |
| Suspend or ban users        | no    | no   | yes       | yes   |
| Manage sources              | no    | no   | optional  | yes   |
| Trigger ingestion           | no    | no   | optional  | yes   |

# 19. Validation Rules Summary

## 19.1 Posts

- `title` is required.
- `post_type` is required.
- `category` is required.
- `link` posts require `url`.
- `text` posts require `body_markdown`.
- `job` posts require `url` or `body_markdown`.

## 19.2 Comments

- `body_markdown` is required.
- `parent_comment_id` must belong to the same post.
- Maximum depth must be enforced.

## 19.3 Votes

- `vote_value` must be `1` or `-1`.
- A user cannot vote on their own content if policy disallows it.

## 19.4 Flags

- `target_type` must be valid.
- `reason_code` must be one of `spam`, `abuse`, `misinformation`, `off_topic`, or `other`.
- Duplicate open flags should be prevented.

# 20. OpenAPI / FastAPI Notes

This spec is intended to map cleanly to FastAPI.

Recommended implementation patterns:

- Pydantic request and response models
- a domain service layer separate from route handlers
- a shared error mapper
- auth dependency injection for current user
- role guards for moderator and admin routes

# 21. Recommended Endpoint Build Order

Build in this order:

1. `/auth/register`
2. `/auth/login`
3. `/auth/me`
4. `/feeds/top`
5. `/feeds/new`
6. `/posts`
7. `/posts/{post_id}`
8. `/posts/{post_id}/comments`
9. `/posts/{post_id}/vote`
10. `/comments/{comment_id}/vote`
11. `/users/{username}`
12. `/flags`
13. moderator routes
14. source and ingestion admin routes

This order matches the shortest path to a functioning MVP frontend.

# 22. Summary

The API is structured around a few key principles:

- feeds are the main read surface
- posts are the main ranked objects
- comments are retrieved flat and rendered as trees client-side
- voting is simple in v1 but future-compatible
- moderation is explicit and auditable
- ingestion has dedicated admin surfaces instead of hidden ad hoc logic

This spec is intentionally conservative. It is designed to be easy to implement, easy to debug, and hard to accidentally destabilize while the product is still finding its shape.
