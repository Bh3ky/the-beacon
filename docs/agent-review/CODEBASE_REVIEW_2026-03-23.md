# CODEBASE_REVIEW_2026-03-23.md

## Scope

Reviewed the current RiftHub repository with emphasis on backend auth, creation, reads, voting, and the browser-facing Next.js client. This is a code review report only; no application files were modified.

## Findings

### High

1. Server-rendered pages are fetching API data without forwarding the caller's auth context, so viewer-specific fields are wrong on first paint.

   `apps/web/lib/api/client.ts` always calls `fetch()` with only the API base URL and request init, but never forwards the incoming request cookies or any auth context. That helper is used by the main SSR pages in [HomePage](/Users/telasi/Developer/RiftHub/apps/web/app/page.tsx:11) and [PostPage](/Users/telasi/Developer/RiftHub/apps/web/app/post/[id]/[slug]/page.tsx:23), as well as the feed and post API helpers. The result is that authenticated users will often render with `viewer_vote = null` and `viewer_can_edit = false` on first load, even if they already voted or own the post/comment.

   That is not just cosmetic: [`VoteControl`](/Users/telasi/Developer/RiftHub/apps/web/components/vote/vote-control.tsx:40) decides whether a click removes a vote or applies one based on `initialViewerVote`. If the server rendered anonymous state, a logged-in user can click an already-active vote and send the wrong action.

2. The auth rate limiter is effectively broken for the intended deployment shape.

   The auth routes bucket attempts by `request.client.host` in [`_client_ip`](/Users/telasi/Developer/RiftHub/apps/api/src/rifthub_api/routes/auth.py:131), then store counters in the process-local [`InMemoryRateLimiter`](/Users/telasi/Developer/RiftHub/apps/api/src/rifthub_api/rate_limit.py:16). In the deployed architecture, browser writes go through the frontend proxy, so the API will usually see the proxy/server IP rather than the real browser IP. That collapses all users behind the same bucket. Because the limiter is also in-memory, counters reset per worker or replica, so throttling can be bypassed by scaling out.

   This weakens the abuse controls on `register`, `login`, `verify`, and `resend-verification` rather than protecting them.

### Medium

3. Verification delivery failures are swallowed after the database commit, which can strand users in a pending state with no surfaced failure.

   [`_dispatch_verification`](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/auth/service.py:129) catches every exception, logs it, and returns success. Both [`register_user`](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/auth/service.py:175) and [`resend_verification`](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/auth/service.py:278) commit the token/user state before calling the dispatcher, so a provider outage leaves the account pending without any API-level signal that delivery failed. The frontend then shows a successful registration or resend flow even though no mail was sent.

   If this is intentional, the code still needs a durable retry signal or delivery-failure state; otherwise users are left to guess why verification never arrives.

### Low

4. The registration UI underreports the real password minimum.

   The backend enforces a 12-character minimum in [`validate_password`](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/auth/security.py:38), but the register form tells users that "8+ characters" is recommended in [`RegisterForm`](/Users/telasi/Developer/RiftHub/apps/web/components/auth/register-form.tsx:141). That mismatch will produce avoidable validation errors and makes the form feel inconsistent with the backend rules.

## Recommendations / Testing Gaps

- Add an integration test for SSR pages that proves viewer-specific fields survive the browser proxy and server-side fetch path, especially vote state and owner-only edit flags.
- Add an auth-throttling test that runs through the deployed proxy shape, or switch the limiter to a shared store with real client identity forwarded explicitly.
- Add a test for verification delivery failure semantics so the intended behavior is explicit instead of implied by logging.

## Open Questions

- Should failed verification delivery be retried asynchronously, or should the API expose a specific "delivery pending/failed" state so the UI can tell the user what happened?
- Is the frontend proxy intended to be the only browser-facing path in production? If so, the API should not rely on `request.client.host` for abuse control.

## Summary

The repo is in reasonably good shape structurally, but three production-facing issues stand out: viewer-aware SSR data is not preserved, auth throttling is proxy- and worker-hostile, and verification delivery failures are silently absorbed after commit. The password-hint mismatch is smaller, but it is still worth fixing because it creates predictable user friction.
