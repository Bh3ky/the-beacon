# Feedback: API Tests

## Security Gaps That I Think Need Filling

**1. Verification token brute-force surface not tested**

- In our test guide we tests that a valid token works and that login is blocked before verification which ticks all the boxes of our current auth flow, but now that I am reading and thinking about extra edge cases:
    - what happens when an expired verification token is submitted?
    - what happens when a used (already consumed) token is submitted a second time?
    - what happens with a malformed/garbage token (not just missing, but plausible-looking random string)?

- a verification token endpoint that returns 400 invalid_token vs 410 token_expired vs 404 leaks information about token state. more critically, if used tokens are not invalidated, an attacker who intercepts a link can re-verify later. perhaps we need to add more three spot checks:

```bash
# expired token
curl -i -H "Content-Type: application/json" \
  -d '{"token":"expired-token-value"}' \
  http://127.0.0.1:8000/v1/auth/verify

# already-used token (resubmit the token from 4.4)
# garbage token
curl -i -H "Content-Type: application/json" \
  -d '{"token":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}' \
  http://127.0.0.1:8000/v1/auth/verify
```


**2. Session fixation is not tested**

- after logout (Step 4.6), the guide confirms cookies are cleared - but there is no check that older session cookie is actually invalid on the server side. a client-side cookie clear with a still-valid server-side session is a session fixation vulnerability. perhaps we need to add:

```bash
# Take the old session cookie value before logout, try to use it after
curl -i -b "rifthub_session=<OLD_SESSION_VALUE>" \
  http://127.0.0.1:8000/v1/auth/me
```

- expected: 401 unauthenticated, not a valid indentity response


**3. CSRF cookie theft via HTTP is not tested**

- the code review checklist (9.1) mentions "CSRF enforcement path" but the manual validation only tests CSRF with a wrong token and with no token. there is no check that the CSRF cookie itself is set with HttpOnly: false (it must be readable by js) but Secure: true (HTTPs only). may we can add:

```bash
# Check cookie flags in the Set-Cookie header
curl -i -c /tmp/rifthub-cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"email":"...","password":"..."}' \
  http://127.0.0.1:8000/v1/auth/login | grep -i set-cookie
```

- we need to verify in the response: session cookie has HttpOnly; SameSite=Lax(or Strict), CSRF cookie doesn't have HttpOnly, both have Secure in production config. 


**4. Rate limiting on auth endpoints is not checked**

- there's no mention of rate limiting on /auth/register, /auth/login, or /auth/verify. since this is going to be a public API, i think these three are highest-value brute-force targets. 


**5. Password enumeration via login response timing/message is not tested**

- Step 4.2 tests that a pending user is blocked, but there is not test for what happens when a user submit:
    - a valid email with wrong password
    - a completely unknown email with any password. 

- both should return the same error code and ideally the same response time. if a valid-but-wrong-password returns 401 invalid_credentials and an unknown-email returns 404 or a different message, you have user enumeration. we need add to Step 8:

```bash
# Unknown email
curl -i -H "Content-Type: application/json" \
  -d '{"email":"doesnotexist@example.com","password":"anything"}' \
  http://127.0.0.1:8000/v1/auth/login
```

## Functional Test Gaps


**6. Unauthenticated read response are not validated for viewer field absence**

- Step 5 runs all read checks without cookies. this is correct for public read access, but none of the expected responses explicitly check that viewer_vote, viewer_can_edit, and viewer_can_moderate are null/false in unauthenticated responses. a missing guard on the viewer-enrichment path could accidentally serialize a previous request’s viewer state. we need to add explicit assertions on these fields in Steps 5.1–5.5.


**7. Pagination is not manually tested**

- the guide validates that page_info.next_cursor and has_next_page are present in the response, but there’s no test that actually follows a cursor. if the DB has fewer than one page of posts, has_next_page will always be false and cursor logic is never exercised manually. wee need to add a step that:
	- creates enough posts to exceed one page
	- fetches the second page using the returned cursor
	- confirms ordering is stable and no items are duplicated or dropped


**8. Comment sort validation is shallow**

- Step 5.5 tests sort=top only. Steps 6.4–6.5 create comments, but the guide never validates sort=new or sort=old manually. For a feature that has three distinct code paths, all three should be spot-checked. 
- perhaps we need:

```bash
curl -i "http://127.0.0.1:8000/v1/posts/<POST_ID>/comments?sort=new"
curl -i "http://127.0.0.1:8000/v1/posts/<POST_ID>/comments?sort=old"
```


**9. Cross-post parent comment injection is not in the manual steps**

- The Slice 3 plan called this out as a required test case, but it’s only mentioned in the automated test file list (9.7). There’s no manual curl command to verify it. Add to Step 6:

```bash
# Create a second post, get its comment ID, then try to reply to it under the first post
curl -i -b /tmp/rifthub-cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  -d '{"body_markdown":"Injected reply","parent_comment_id":"<COMMENT_ID_FROM_OTHER_POST>"}' \
  http://127.0.0.1:8000/v1/posts/<POST_ID>/comments
```

- expected: 422 or 404, not a successfull cross-post comment link


**10. Job post expiry edge cases are absent from manual checks**

- Step 5.3 checks the jobs feed returns a 200 — but the most important jobs feed behavior (filtering expired jobs) is left entirely to the automated suite. Add a manual spot check: create a job post with a job_expires_at in the past, then confirm it doesn’t appear in the feed response.



**11. Voting on a non-existent target is not manually tested**

- Step 8.1 tests voting without auth. But there’s no manual check for voting on a post ID that doesn’t exist. Add to Step 8:

```bash
curl -i -b /tmp/rifthub-cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  -d '{"vote_value":1}' \
  http://127.0.0.1:8000/v1/posts/00000000-0000-0000-0000-000000000000/vote
```

- expected: 404 post_not_found.


## Code Review Checklist Gaps


**12. Resend verification flow is not in the manual steps**

- Section 9.2 mentions “resend flow correctness” as a code review item, but there’s no manual validation step for it anywhere in Steps 3–8. The resend path has its own risk surface: can you resend for an already-active account? Can you flood the endpoint to spam a user’s inbox? Add a Step 4.x:

```bash
# Resend before verification
curl -i -H "Content-Type: application/json" \
  -d '{"email":"phase3user+02@example.com"}' \
  http://127.0.0.1:8000/v1/auth/resend-verification

# Resend after verification (should be a no-op or 400)
# same command after step 4.4
```


**13. Code review section 9.4 does not mention unicode slug edge cases.**

- the Slice 3 review flagged non-ASCII titles as an important slug generation edge case. The code review checklist for the creation layer should explicitly call this out:
	- slug generation handles non-ASCII input (transliteration or safe-char stripping)
	- slug generation has a max length cap
	- slug generation has a fallback for degenerate titles


**14. The write_access.py review checklist is too brief

- Section 9.5 references write_access.py for the suspended/banned check but only mentions it in passing. This is a shared security guard used by creation and voting routes. The review should explicitly check:
	- the guard is a Depends() injection, not a copy-pasted function
	- it checks account status from the current session, not a stale value
	- it returns 403 forbidden before any DB write is attempted


## Minor Points

- Step 3 instructions assume rifthub_csrf is the cookie name. If the cookie name ever changes in config, the awk extractor silently returns nothing and the CSRF steps all fail mysteriously. Worth noting the cookie name comes from config and should match what’s set in the login response headers.

- Step 6.1 saves <POST_ID> but doesn’t remind the reader to export it as a shell variable. Since subsequent steps reference $POST_ID implicitly, a one-liner like export POST_ID=<id from response> would prevent copy-paste errors across steps.

- Step 7.3 says “score changes by -2 relative to the prior +1 state” — this is correct but the guide doesn’t explain how to verify the delta from the raw response. The manual check should show the expected before/after values: upvote_count decreases by 1, downvote_count increases by 1, score decreases by 2.

- The guide has no step for testing vote behavior on a post that the voter authored. Even though self-vote restriction is explicitly deferred in Slice 4, it’s worth a one-line note in Step 7 confirming self-voting is allowed in the current build — so when the restriction is later added, there’s a clear before/after baseline.