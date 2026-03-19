# Phase 4 Frontend Test And Code Review Guide

Date: `2026-03-19`
Status: `ready to follow`

## Purpose

Use this guide to:

- manually validate the live Phase 4 frontend against the real backend
- review the frontend code in a controlled order
- check that the browser auth/write flows are sound
- catch UI regressions, proxy mistakes, and client/server boundary slop

This is the frontend equivalent of the earlier API validation guide.

## Current Scope Covered

The current Phase 4 core frontend includes:

- public feeds:
  - `/`
  - `/new`
  - `/ask`
  - `/show`
  - `/jobs`
- post detail:
  - `/post/[id]/[slug]`
- auth:
  - `/login`
  - `/register`
  - `/verify`
- submit:
  - `/submit`
- authenticated browser writes:
  - submit post
  - add top-level comment
  - reply to comment
  - post voting
  - comment voting
  - logout from header

## Before You Start

## Services

Run these in separate terminals:

```bash
npm run db:up
```

```bash
npm run api:dev
```

```bash
npm run web:dev
```

## Optional Dev Feed Seed

If you want the richer homepage/feed data from the mockup-inspired backend seed:

```bash
npm run db:seed:feed
```

## Sanity Checks

Confirm these load:

```bash
curl http://127.0.0.1:8000/health
```

```bash
curl http://127.0.0.1:8000/v1/feeds/top
```

Open in browser:

- `http://127.0.0.1:3000/`
- `http://127.0.0.1:3000/login`

If the frontend shows empty or fallback states after backend changes, restart the API. New routes require the API process to reload.

## Manual Frontend Validation

## 1. Foundation And Shell

Verify:

- the app is framed inside the darker browser canvas
- the shell is centered and `max-w-6xl`
- no rounded shell corners
- shell bleeds top and bottom of viewport
- accent orange header sits inside the app shell, not full browser width
- typography visually matches:
  - headings/display: editorial serif
  - metadata/controls/body: mono

Check:

- homepage on desktop
- homepage on mobile width
- post detail on desktop
- auth pages on desktop and mobile

## 2. Header And Footer

Verify:

- header nav tabs work:
  - `top`
  - `new`
  - `ask`
  - `show`
  - `jobs`
- `submit` link works
- login state changes header behavior
- after login:
  - username appears
  - `logout` appears
- after logout:
  - header returns to logged-out state

Footer:

- appears inside the shell
- visual style matches the dark editorial system
- links render without breaking layout

## 3. Public Feed Surfaces

Visit:

- `/`
- `/new`
- `/ask`
- `/show`
- `/jobs`

Verify on each:

- feed rows render from real backend data
- category badges match the post category
- domain display appears when domain exists
- comment counts link to post detail
- post title links to `/post/[id]/[slug]`
- `more →` works when cursor exists

For `/jobs` specifically:

- items look visually consistent with the rest of the app
- expired jobs should not appear if the backend is filtering correctly

## 4. Post Detail And Comments

Open a real post detail page.

Verify:

- title, score, author, time, and domain render correctly
- body text appears if the post is text/job content
- comments render as a nested tree
- author badge appears on the post author’s comments
- sort links work:
  - `top`
  - `new`
  - `old`

Check nested replies:

- indent ladder colors are visible
- reply nesting is readable
- no layout breakage on deeper threads

## 5. Register Flow

Go to `/register`.

Test:

1. Create a new account with a fresh username/email.
2. Confirm you get a success state, not an authenticated session.
3. Confirm the UI clearly says verification is required.
4. Use the resend action and confirm it does not break.

Verify:

- account is not treated as logged-in immediately after register
- the UI reflects the verification-first contract
- duplicate username/email errors render cleanly

## 6. Verify Flow

Go to `/verify`.

Test both:

1. Open `/verify?token=<TOKEN>`
2. Paste a token manually into the field

Verify:

- successful verify activates the session
- after success, refresh-sensitive surfaces behave like logged-in state
- invalid token shows an error state
- expired token shows an error state

If using local log delivery or Mailpit, obtain the real token from there.

## 7. Login And Logout

Go to `/login`.

Test:

1. log in with a verified account
2. confirm redirect works
3. confirm header shows authenticated state
4. click `logout`
5. confirm header returns to logged-out state

Also test:

- wrong password
- unknown email
- pending account login

Verify:

- pending account path exposes resend affordance
- invalid credentials do not break layout
- logout actually clears browser session behavior

## 8. Submit Flow

Go to `/submit`.

While logged out:

- confirm you see CTA state, not fake submission

While logged in:

1. create a text post
2. create a link post
3. create a job post

Verify:

- submit redirects to the created post detail page
- category select works
- job expiry input only appears for job posts
- link URL field appears only when relevant
- body field appears only for text/job where intended

## 9. Comment Submission

On a post detail page while logged in:

1. add a top-level comment
2. confirm page refresh shows the new comment
3. reply to an existing comment
4. confirm nested reply appears in the correct branch

While logged out:

- trying to comment should direct you toward login, not silently fail

## 10. Voting

Test on feed rows:

1. upvote a post
2. confirm score changes
3. click same upvote again
4. confirm vote is removed / score returns appropriately
5. downvote a post

Test on post detail:

- repeat the same post-vote checks

Test on comments:

1. upvote comment
2. remove vote
3. downvote comment

Verify:

- vote colors/states change visibly
- no duplicate button spam while request is in flight
- unauthenticated voting redirects to login flow with `next`

## 11. Auth Redirect Behavior

From a logged-out state:

- click vote on a post
- click vote on a comment
- try to comment

Verify:

- you are sent to `/login?next=<current-path>`
- after successful login, you land back on the intended page

## 12. Failure And Resilience Checks

Temporarily stop the API and refresh a frontend page.

Verify:

- homepage feed shows unavailable/empty fallback state
- stats strip shows fallback state instead of crashing
- auth pages still render their shell cleanly

Restart the API afterward.

## 13. Responsive Pass

Check at minimum:

- mobile width around `390px`
- tablet width around `768px`
- desktop width

Verify:

- feed rows do not collapse awkwardly
- long post titles wrap cleanly
- auth shell stacks properly on smaller screens
- comment tree remains readable on narrow widths
- submit form stays usable on mobile

## Code Review Order

Review in this order so the architecture reads from outer shell to browser writes.

## 1. App Entry And Shared Shell

Start here:

- [layout.tsx](/Users/telasi/Developer/RiftHub/apps/web/app/layout.tsx)
- [globals.css](/Users/telasi/Developer/RiftHub/apps/web/app/globals.css)
- [app-shell.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/layout/app-shell.tsx)

Check:

- theme tokens are centralized
- typography scale matches the locked plan
- shell framing logic is not duplicated elsewhere
- no random one-off colors overriding token intent

## 2. Layout Components

Review:

- [site-header.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/layout/site-header.tsx)
- [header-auth.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/auth/header-auth.tsx)
- [site-footer.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/layout/site-footer.tsx)
- [stats-strip.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/layout/stats-strip.tsx)

Check:

- header remains thin and compositional
- auth state is not duplicated in multiple components
- logout flow stays centralized
- fallback states are explicit, not misleading

## 3. API Client And Browser Proxy

Review:

- [client.ts](/Users/telasi/Developer/RiftHub/apps/web/lib/api/client.ts)
- [browser-api.ts](/Users/telasi/Developer/RiftHub/apps/web/lib/browser-api.ts)
- [route.ts](/Users/telasi/Developer/RiftHub/apps/web/app/api/[...path]/route.ts)
- [use-current-user.ts](/Users/telasi/Developer/RiftHub/apps/web/lib/use-current-user.ts)
- [types.ts](/Users/telasi/Developer/RiftHub/apps/web/lib/api/types.ts)

This is one of the most important review areas.

Check:

- browser writes stay same-origin through the proxy
- CSRF header logic is centralized
- credentials handling is not duplicated per component
- error handling is consistent
- route proxy does not accidentally strip required headers or cookies

## 4. Feed Layer

Review:

- [page.tsx](/Users/telasi/Developer/RiftHub/apps/web/app/page.tsx)
- [new/page.tsx](/Users/telasi/Developer/RiftHub/apps/web/app/new/page.tsx)
- [ask/page.tsx](/Users/telasi/Developer/RiftHub/apps/web/app/ask/page.tsx)
- [show/page.tsx](/Users/telasi/Developer/RiftHub/apps/web/app/show/page.tsx)
- [jobs/page.tsx](/Users/telasi/Developer/RiftHub/apps/web/app/jobs/page.tsx)
- [feed-page.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/feed/feed-page.tsx)
- [feed-row.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/feed/feed-row.tsx)
- [feed-list.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/feed/feed-list.tsx)
- [feed-empty-state.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/feed/feed-empty-state.tsx)
- [category-badge.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/feed/category-badge.tsx)
- [feed.ts](/Users/telasi/Developer/RiftHub/apps/web/lib/feed.ts)

Check:

- no feed page is reimplementing the same shell logic badly
- category mapping is intentional
- vote control integration in feed rows stays thin
- cursor pagination is honest and not faked

## 5. Post Detail And Comments

Review:

- [post/[id]/[slug]/page.tsx](/Users/telasi/Developer/RiftHub/apps/web/app/post/[id]/[slug]/page.tsx)
- [post-header.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/post/post-header.tsx)
- [comment-thread.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/post/comment-thread.tsx)
- [comment-composer-shell.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/post/comment-composer-shell.tsx)
- [comments.ts](/Users/telasi/Developer/RiftHub/apps/web/lib/comments.ts)

Check:

- tree reconstruction is deterministic
- reply flow is local and not duplicated across branches
- top-level and reply comment submission share the same core logic
- vote controls do not create state drift obvious to the user
- client components are used only where interaction is required

## 6. Auth Surfaces

Review:

- [login/page.tsx](/Users/telasi/Developer/RiftHub/apps/web/app/login/page.tsx)
- [register/page.tsx](/Users/telasi/Developer/RiftHub/apps/web/app/register/page.tsx)
- [verify/page.tsx](/Users/telasi/Developer/RiftHub/apps/web/app/verify/page.tsx)
- [auth-shell.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/auth/auth-shell.tsx)
- [login-form.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/auth/login-form.tsx)
- [register-form.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/auth/register-form.tsx)
- [verify-form.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/auth/verify-form.tsx)
- [form-field.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/auth/form-field.tsx)

Check:

- auth pages respect the verification-first backend contract
- no component assumes register means authenticated
- resend path is usable and not hidden in an awkward place
- field-level vs form-level errors are handled deliberately
- the auth shell is reused cleanly, not copy-pasted

## 7. Submit Surface

Review:

- [submit/page.tsx](/Users/telasi/Developer/RiftHub/apps/web/app/submit/page.tsx)
- [submit-form.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/submit/submit-form.tsx)

Check:

- logged-out state is explicit
- logged-in submission path is real, not half-mocked
- form branching by post type is coherent
- payload shape matches the backend

## 8. Vote Primitive

Review:

- [vote-control.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/vote/vote-control.tsx)

Check:

- same-value vote removes correctly
- post/comment branching stays readable
- no route-specific assumptions are baked into the primitive
- login redirect behavior is centralized and sane

## Code Review Questions

Use these questions while reading:

- Is this logic in the right layer?
- Is this client component truly necessary?
- Is any auth/CSRF logic duplicated where it should be shared?
- Is any route file doing too much?
- Does this component depend on mock data or real backend contracts?
- Would a backend error leave the UI misleadingly blank?
- Is any file getting too large or mixing unrelated concerns?
- Would this behavior still make sense under a slow network or double-click?

## Size And Modularity Check

Your stated review preference is that files should not drift into large mixed-concern blobs.

When reviewing, push back on:

- route files that embed heavy client logic
- large client components that mix UI, auth, networking, and data transforms
- repeated auth/session checks across unrelated components
- repeated API error-shaping logic

Preferred pattern:

- thin route/page components
- small reusable client primitives
- centralized browser API helpers
- centralized tree/format transforms in `lib/`

## Quick Regression Checklist

If you want a short smoke pass after code edits, recheck:

1. `/` loads live feed
2. `/ask` and `/show` load real feed data
3. `/login` and `/register` render correctly
4. `/verify?token=...` works
5. `/submit` works when authenticated
6. top-level comment submission works
7. reply works
8. post vote works
9. comment vote works
10. logout updates the header

## Build Verification

Use this before calling the slice stable:

```bash
npm --workspace @rifthub/web run build
```

If you changed backend routes used by the frontend, also restart the API and recheck the affected pages.

## Review Outcome Template

When you finish your review, summarize findings in this shape:

```text
Findings
1. ...
2. ...

Open questions
1. ...
2. ...

Passed checks
- ...
- ...
```

That keeps the review actionable instead of turning into a vague aesthetics pass.
