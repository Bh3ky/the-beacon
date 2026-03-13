# API_SPEC Review

## Session

- Date: 2026-03-13
- Stage: Phase 0 - Docs review
- Source reviewed this session: `docs/API_SPEC.md`

## Syntax cleanup completed

I made safe consistency fixes directly in `docs/API_SPEC.md`:

- aligned the auth model with the resolved HTTP-only cookie-session decision
- removed Bearer-token example language from the auth section
- clarified login and logout session behavior
- tied `flags.reason_code` to the enum-backed moderation reasons
- updated the ingestion example away from the older `queued` item state
- tightened the validation summary for flags

These were contract-alignment edits, not an endpoint redesign.

## Findings

### 1. Authentication wording had drifted from the resolved v1 auth decision

Before this review, `API_SPEC.md` still described authentication as:

- cookie-based session auth or
- Bearer token auth

It also used Bearer headers in examples and allowed login responses to return a token payload depending on implementation.

Impact:

- high
- this would create confusion for frontend auth handling, middleware, CSRF, and backend session storage

Action taken:

- updated the file to document HTTP-only cookie-session auth as the v1 contract
- added the required cookie/session properties and explicit CSRF mention
- updated login/logout notes so they match a session-cookie flow

### 2. Flag reason validation needed to match the schema decision

The API examples already used values like `spam`, but the spec did not explicitly tie `reason_code` to the enum-backed moderation reasons approved in `DATABASE_SCHEMA.md`.

Impact:

- medium
- without an explicit allowed set, clients and dashboards can drift into inconsistent moderation data

Action taken:

- documented the allowed reason codes in the flag object section
- tightened the validation summary to list the accepted values

### 3. Ingestion item examples were still using an older status

The ingestion admin section still showed:

- `ingestion_status: "queued"`

But the resolved schema direction now uses the richer persisted lifecycle:

- `discovered`
- `normalized`
- `duplicate`
- `classified`
- `awaiting_review`
- `published`
- `rejected`
- `failed`

Impact:

- medium to high
- affects worker implementation, admin UI filters, and API client assumptions

Action taken:

- replaced the outdated example state with `awaiting_review`
- documented the expected persisted ingestion lifecycle in the ingestion section

Follow-up note:

- `INGESTION_PIPELINE.md` should be checked for the same vocabulary when its turn comes in the fixed review order

### 4. The post detail route is not actually a conflict, but it should stay explicit

`API_SPEC.md` uses:

- `GET /posts/{post_id}/{slug}`

The resolved frontend route is:

- `/post/[id]/[slug]`

Impact:

- low
- the distinction is acceptable, but it should remain intentional so frontend and backend route docs do not get treated as contradictory

Recommendation:

- keep the REST API route plural unless there is a strong reason to mirror the frontend path exactly
- keep the frontend route decision documented separately as a UI routing concern

## Clarification answers received

Resolved on 2026-03-13:

1. FastAPI auth should use server-side cookie sessions rather than a token-returning auth flow.
2. CSRF validation should be enforced on mutating routes with `validate_csrf`-style dependency checks.
3. Origin validation middleware should run for state-changing requests.
4. The frontend should bootstrap the CSRF token on app mount, store it in memory only, and auto-attach it to mutating requests.
5. `localStorage` should not be used for the CSRF token.
6. Credentialed cross-origin requests are required, so CORS must use `allow_credentials=True` with explicit allowed origins only.

Implementation note:

- keep the auth flow consistent with the resolved cookie-session direction and avoid reintroducing Bearer-token semantics later in backend or frontend docs

## Recommendation for next session

Next source file in the fixed order:

- `docs/RANKING_SYSTEM.md`

Reason:

- auth, flags, and ingestion wording are now aligned more closely between schema and API
- the next important source of implementation truth is the ranking behavior that will shape feed queries and cache strategy
