# CODEBASE_FIX_PLAN_2026-03-24

## Scope

This plan turns the findings in `docs/agent-review/CODEBASE_REVIEW_2026-03-23.md` into a small set of implementation PRs. It follows the local repo guidance in `docs/agent-review/MEMORY.md` and `COMMANDS.md`. `AGENTS.md` is currently empty, so it adds no extra constraints.

Guardrails applied from local repo docs:

- keep changes in vertical slices
- avoid broad rewrites and second sources of truth
- keep auth and moderation/security logic server-side
- prefer production-safe behavior over silent fallbacks
- use the existing same-origin web proxy pattern intentionally, not inconsistently

External references used to ground the plan:

- Next.js `cookies()` and `headers()` docs for request-bound Server Component data access and header forwarding
- FastAPI and Uvicorn proxy docs for trusted forwarded headers and real client identity handling
- Redis and Upstash rate-limiting docs for shared, multi-instance-safe throttling
- Resend webhook docs for durable email delivery state and retry-aware handling

## PR 1: Fix Auth-Aware SSR Reads

### Goal

Make server-rendered feed and post pages send the viewer's auth context to the API so `viewer_vote`, `viewer_can_edit`, and similar fields are correct on first paint.

### Why this first

This is the most visible product bug. It affects core read surfaces and makes logged-in state inconsistent between SSR and client-side mutations.

### Source-backed implementation direction

- Next.js documents that `cookies()` can read incoming request cookies in Server Components.
- Next.js documents that `headers()` can read incoming request headers in Server Components, and explicitly shows forwarding auth headers in a server-side `fetch`.
- The correct pattern here is to make the server-side fetch path intentionally request-bound instead of relying on ambient server state.

### Planned code changes

- Introduce a dedicated server-only API fetch helper for App Router server components.
- In that helper, read incoming cookies with `cookies()` and forward them to the backend as a `Cookie` header.
- Optionally forward a narrow allowlist of request headers only if they are needed for observability or downstream identity propagation. Do not blindly mirror every header from the incoming request.
- Keep the browser-side proxy flow unchanged for client mutations unless a concrete bug requires touching it.
- Update the SSR read helpers used by:
  - `/`
  - `/new`
  - `/ask`
  - `/show`
  - `/jobs`
  - `/post/[id]/[slug]`
- Make the helper naming explicit so browser fetches and server fetches cannot be confused again.

### Tests

- Add a web-side integration test or route-level test proving that an authenticated server-rendered request forwards cookies and receives viewer-aware payload fields.
- Add a regression test for the post detail page path, since it exercises both post and comment reads.
- Preserve current API read tests; they already validate viewer-aware backend behavior in isolation.

### Out of scope

- Changing the public API contract
- Reworking the existing browser `/api/[...path]` proxy beyond what is necessary for testability

### Acceptance criteria

- Logged-in SSR renders show the correct existing vote state on first paint.
- Viewer edit/moderation flags are correct before hydration.
- No new anonymous-only regressions on public pages.

## PR 2: Replace Proxy-Host-Based Auth Throttling

### Goal

Move auth throttling off process-local memory and off naive `request.client.host` identity so rate limits still work behind the frontend proxy and across multiple API instances.

### Why this is urgent

The current logic is not production-safe for a Vercel -> API proxy shape and can be weakened by horizontal scaling.

### Source-backed implementation direction

- FastAPI documents that proxy headers need explicit trusted handling when the app is behind a proxy.
- Uvicorn documents `X-Forwarded-For`, `X-Forwarded-Proto`, `--proxy-headers`, and `--forwarded-allow-ips`, and explicitly warns to trust only known proxy clients.
- Redis documents rate-limiter patterns using atomic `INCR` plus `EXPIRE`.
- Upstash documents fixed-window and sliding-window algorithms for shared distributed limits.

### Planned code changes

- Add a production rate-limit backend backed by Redis or Upstash Redis.
- Keep the in-memory limiter only for local development/tests if that materially simplifies setup.
- Replace `_client_ip()` with a trusted client-identity function:
  - prefer a trusted forwarded chain when the request came through known proxy infrastructure
  - fall back to `request.client.host` only in local or non-proxied environments
- Apply the shared limiter to:
  - `register`
  - `login`
  - `verify`
  - `resend-verification`
- Keep per-account and per-IP style buckets, but define them explicitly and document the rationale:
  - IP or client fingerprint for abuse fanout
  - canonicalized email/account key for targeted brute-force protection
- Add explicit settings for trusted proxy IPs or forwarded-header trust so production behavior is deliberate.

### Algorithm choice

- Prefer a simple shared fixed window for the first corrective PR if speed matters most.
- If boundary burst behavior is a concern, use a sliding window implementation.
- Do not ship another per-process memory limiter as the production path.

### Tests

- Add unit tests for trusted forwarded-header parsing and fallback behavior.
- Add limiter tests proving that repeated requests on the same logical client key trigger `429`.
- Add tests that verify canonical email-based buckets still work when email normalization succeeds.

### Operational checklist

- Document the required env vars for Redis/Upstash.
- Document trusted proxy configuration for local, staging, and production.
- Confirm the deployed API runtime actually enables trusted proxy header handling.

### Acceptance criteria

- Limits apply per logical client, not per proxy hop.
- Limits remain effective across multiple API workers.
- Rate-limit behavior is deterministic and documented.

## PR 3: Make Verification Delivery Failures Explicit And Durable

### Goal

Stop silently absorbing verification delivery failures after commit. Replace the current "log and pretend success" flow with explicit delivery state and a retryable design.

### Why this should be a separate PR

This is partly a product-contract decision, not only a code fix. It touches backend behavior, frontend messaging, and possibly persistence.

### Source-backed implementation direction

- Resend documents webhook-based delivery notifications and retries.
- That supports a more reliable model where send attempts and delivery outcomes are tracked explicitly instead of inferred from logs.
- For this repo, the safest medium-term design is commit durable state first, then perform delivery with observable status transitions.

### Recommended implementation shape

- Change `_dispatch_verification()` to return a structured result instead of swallowing exceptions.
- Introduce durable delivery state. Exact shape can be one of:
  - fields on the verification token row
  - fields on the user row
  - a dedicated delivery-attempt/outbox table
- Preferred direction:
  - create durable send intent in the same transaction as the token
  - send asynchronously or synchronously via a worker/service step
  - store provider response identifiers where available
  - update status from provider responses and, later, webhook events

### Minimum acceptable correction in this PR

- Do not silently return success when provider dispatch fails.
- Return an explicit API-visible outcome for resend failures.
- Return a structured registration outcome that allows the frontend to say one of:
  - verification email sent
  - delivery pending
  - delivery failed, retry available
- Update the register and resend UI copy so the user is not misled.

### Better long-term shape

- Add webhook ingestion for Resend delivery events.
- Track sent, delivered, bounced, and failed states.
- Retry based on durable pending/failed records instead of only ad hoc user actions.

### Tests

- Add backend tests for:
  - provider success
  - provider failure
  - resend behavior on failure
  - persistence of delivery state
- Add frontend tests for the new user-facing registration/resend messages.

### Acceptance criteria

- Delivery failure is visible in API behavior and UI behavior.
- Pending accounts are not left in a silent failure state.
- The system has a clear path to retries and auditability.

## Small Fix To Fold Into PR 1 Or PR 3

### Password hint mismatch

Update the register form hint to match the backend minimum of 12 characters.

This is low risk and should ride along with whichever PR touches auth UI first.

## Suggested PR Order

1. PR 1: Fix auth-aware SSR reads
2. PR 2: Replace proxy-host-based auth throttling
3. PR 3: Make verification delivery failures explicit and durable

## Suggested Review Notes For Each PR

- keep helper boundaries explicit so browser and server fetch logic do not drift together again
- avoid introducing hidden environment fallbacks for security-sensitive behavior
- prefer adding targeted regression tests with the fix, not after
- document every new runtime assumption in `COMMANDS.md` or the relevant implementation doc once code lands

## References

- Next.js `cookies()` docs: https://nextjs.org/docs/app/api-reference/functions/cookies
- Next.js `headers()` docs: https://nextjs.org/docs/app/api-reference/functions/headers
- Next.js `fetch()` docs: https://nextjs.org/docs/app/api-reference/functions/fetch
- FastAPI behind a proxy: https://fastapi.tiangolo.com/advanced/behind-a-proxy/
- Uvicorn deployment and forwarded headers: https://www.uvicorn.org/deployment/
- Redis `INCR` rate-limiter patterns: https://redis.io/docs/latest/commands/incr/
- Redis rate-limiting best practices: https://redis.io/glossary/rate-limiting/
- Upstash ratelimiting algorithms: https://upstash.com/docs/redis/sdks/ratelimit-ts/algorithms
- Resend webhooks: https://resend.com/docs/webhooks/introduction
