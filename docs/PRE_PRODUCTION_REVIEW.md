# RiftHub — Pre-Production Review

**Stance:** senior-engineer review, "would I put this on the public internet as a portfolio piece?"
**History:** first pass October 2026, re-verified against a live stack the same month, fixes applied through November 2026.
**This document:** the status report. Every finding from the review is listed with where it stands.

---

## 1. Summary

The review found 4 blockers, 8 should-fix items and 3 newly discovered bugs. **All 4 blockers and all 11 other numbered findings are now fixed in code and verified.** What remains is deployment work (hosting, a real email domain, a first CI run) and optional hardening. None of the remaining items is a known bug that affects the demo loop.

| | Count | Status |
|---|---|---|
| Blockers (B-1 to B-4) | 4 | Fixed |
| Should-fix (S-1 to S-8) | 8 | Fixed |
| Newly found during live testing (N-1 to N-3) | 3 | Fixed |
| Remaining items | see §4 | Open |

---

## 2. Findings and their status

Findings marked **repro** were reproduced against a live database before being fixed.

### Blockers

| ID | Finding | Fix | Verified |
|---|---|---|---|
| B-1 | Rate limits existed only on auth routes. 150 comments in seconds all succeeded. **repro** | A per-user rate-limit guard on posting (5/hour), commenting (20/min), voting (60/min) and flagging (10/min), in `dependencies.py` | Live: 7 posts gave 5×201 then 429; 25 comments gave 20×201 then 429; a second user was unaffected |
| B-2 | Client IP was untrustworthy behind the Next proxy: a rotating `X-Forwarded-For` bypassed every IP limit. **repro** | The proxy strips browser IP headers and sends the platform IP plus a shared `RIFTHUB_PROXY_SECRET`. The API honors the forwarded IP only when the secret matches | Live: fake or wrongly-signed headers are ignored; the correct secret gives each IP its own bucket. **Caveat below** |
| B-3 | No input length limits: a 301-character title returned 500, a 1 MB body was accepted. **repro** | `Field(max_length=...)` on titles (300), URLs (2048), post bodies (20,000), comments (10,000) and flag notes (1,000) | Live: all return 422 with a clear message |
| B-4 | Production would silently misbehave: no email sent, links pointing at localhost | The API refuses to start in production unless secrets, HTTPS origins and Resend email are configured. `.env.example` is complete | Unit tests cover one valid and seven invalid configurations |

**B-2 caveat.** The proxy takes the client IP from the last `X-Forwarded-For` entry. That is correct on Vercel, which overwrites the header with the real client IP. On a plain local run, or any host with no overwriting proxy in front of Next, a browser can still fake it. The deployment notes must say this.

### Should-fix

| ID | Finding | Fix | Verified |
|---|---|---|---|
| S-1 | Vote counters lost updates under concurrency: 25 voters left a counter of 24. **repro** | Counters are updated with `column = column + n` in the database, with the new values returned. Duplicate adds return 409, and a repeated remove is ignored | Live: 25 concurrent voters give 25 and 25 on posts and comments; 10 concurrent removes by one user change the count exactly once; 0 mismatches across all rows |
| S-2 | Open redirect after login and verify through `?next=` | A `safeRedirectPath` helper accepts only same-site paths | Frontend unit tests plus a browser check |
| S-3 | A 403 (for example voting on your own post) sent logged-in users to the login page | Only 401 redirects to login; other errors show the server's message | Browser check |
| S-4 | Docs and code disagreed (downvotes, edit window, repost window, hashing, lockout) | Docs updated to describe what is built; unbuilt items are marked "not implemented yet"; `API_SPEC.md` gained an implemented-routes table | Read-through |
| S-5 | Password hashing (about 185 ms) froze the whole server | Hashing runs in a worker thread | Measured: worst event-loop freeze 185 ms before, 7 ms after; a test guards it |
| S-6 | One failing test (the `.env` leak) and no CI | `conftest.py` isolates the environment for every test (this also fixed 9 other tests that quietly depended on `.env`). A GitHub Actions workflow runs lint, tests, build and type-check | Suite passes with a stripped environment, as in CI. **The workflow has not run on GitHub yet** |
| S-7 | Homepage stats ran 10 queries on every page load | A 60-second in-process cache with a lock so simultaneous requests share one query | Three tests |
| S-8 | Raw upstream errors and developer wording in the UI; feed pages showed an empty feed when the API failed | New `error.tsx` and `not-found.tsx`; feed pages no longer swallow errors; homepage wording fixed | Browser check |

### Found during live testing

| ID | Finding | Fix |
|---|---|---|
| N-1 | Any non-JSON request body returned 500: the validation handler tried to serialize raw bytes | The handler returns only `type`, `loc` and `msg`, and a test covers it |
| N-2 | `/post/not-a-uuid/x` returned a 500 page | A 404 or 422 from the API now shows the not-found page |
| N-3 | No security headers, `X-Powered-By` exposed, no `robots.txt` | HSTS, nosniff, frame denial, referrer and permissions policies, a production CSP, `robots.txt`. Verified against a production build |

**N-3 notes.** The CSP is production-only because Next's dev mode needs permissions the policy forbids. It still allows inline scripts (`'unsafe-inline'`), which Next needs without per-request nonces. After deploying, check the browser console for "Refused to load" messages.

### Other fixes made along the way

- Ruff installed and enforced; about 160 lint findings fixed; `npm run lint:py` added.
- VS Code pointed at the project virtualenv.
- Production config fails fast with one message listing every problem.
- A MIT `LICENSE` file added; the README rewritten with an honest status, limitations and roadmap.
- Generated files (`next-env.d.ts`, `tsconfig.tsbuildinfo`) no longer tracked.
- Missing migrations on the dev database applied (see the deployment note below).

---

## 3. Evidence that the foundation is sound

| Check | Result |
|---|---|
| API tests | 216 passing |
| Worker tests | 13 passing |
| Frontend unit tests | 3 passing |
| Ruff | clean |
| `tsc --noEmit` and `next build` | clean |
| Migrations | `upgrade head` clean; `alembic check` reports no drift from the models; full downgrade and re-upgrade work |
| Worker | all five jobs run against real Postgres and Redis |
| Security design | hashed opaque sessions, per-session CSRF, `Origin` check, dummy-hash timing parity on login, no email in public payloads, no HTML injection surface (content is rendered as plain text) |

Limits of this evidence: the Python tests run against fakes, so real-database behavior (races, constraints) was verified only by scripted live runs that are **not saved in the repo**. There is no browser or end-to-end test suite, and the Playwright and Chrome DevTools tools failed to connect during the review, so there was **no visual, mobile or accessibility review**.

---

## 4. Still open

### Before a public deploy

| Item | Notes |
|---|---|
| Choose and set up hosting | Web, API, worker, Postgres and Redis. The docs imply Vercel plus Railway; Railway's header handling was not verified |
| Run `npm run db:upgrade` in the deploy pipeline | The dev database was found 4 migrations behind, producing a 500 on registration. Migrations must run before the new API starts |
| Verified sending domain for Resend | The sandbox sender only delivers to your own account address. Needs a domain and DNS records |
| First CI run on GitHub | The workflow is untested remotely. If `npm ci` fails, regenerate `package-lock.json` |
| Request-body size cap | Field limits stop large fields, but a huge request is still read in full. Cap it at the proxy or server |
| Registration race | Two simultaneous sign-ups with the same username or email can raise an unhandled database error (500). Catch the integrity error and return 409 |
| `docs/DEPLOYMENT.md` | Launch order, environment variables, the B-2 caveat, the CSP check |
| Error monitoring and readiness check | `/health` returns a static "ok" without checking the database or Redis |
| Database backups | Documented in `SECURITY.md`, not set up |

### Optional hardening and polish

| Item | Notes |
|---|---|
| Real-database test suite | Turn the scripted live checks (vote races, rate limits, migrations) into repo tests against the compose Postgres |
| Browser tests | A Playwright smoke test of the main pages |
| Screenshots and a demo link in the README | The biggest remaining presentation gain |
| Pin `next`, `react` and `react-dom` | `apps/web/package.json` uses `latest` |
| Stricter CSP | Remove `'unsafe-inline'` using nonces |
| Per-page titles and Open Graph metadata | Only a global title exists |
| Feed snapshots | The worker writes them to Redis but nothing reads them. Wire them in or remove the job |
| Reconcile job scale | It loads every post and comment hourly and rewrites every row. Compare integer counters only, or do it in SQL |
| Comment thread limit | Reads silently stop at 500 comments per post |
| Ingestion fetch | No response-size cap, and the User-Agent contains a placeholder address |
| Proxy methods | The Next proxy only forwards GET, POST and DELETE |
| Container binding | `npm run start` binds `127.0.0.1`, which is unreachable inside a container |
| Repeated `/auth/me` calls | Each client component fetches it separately; a shared context would reduce requests |
| Argon2id | PBKDF2 at 600,000 rounds is acceptable today; Argon2id is the current first choice. The stored hash names its algorithm, so a later upgrade can happen at next login |

### Product gaps (documented, not bugs)

No post or comment editing or deletion, password reset, user profiles, search, topic tag pages, new-account throttling, or automated vote-manipulation detection. All are listed in the README's known limitations and marked in the specs.

---

## 5. Decisions still needed

1. **Deployment target** for each service, and whether the worker runs as a separate service.
2. **A domain for email and the site.** This unblocks Resend and the production configuration.
3. **Feed snapshots:** keep and wire in, or remove.
4. **Whether to build** editing, password reset and profiles before showcasing, or ship with the documented limitations.

---

## 6. Suggested order from here

1. Fix the registration race (small, backend) and add a body-size cap.
2. Push the repository and watch the first CI run; fix anything it finds.
3. Pick the hosting and a domain; write `docs/DEPLOYMENT.md` as you go.
4. Deploy, run migrations, seed sources and starter content, create an admin.
5. Run the smoke-test list in `PORTFOLIO_LAUNCH_CHECKLIST.md` on the deployed site, adding these cases:
   - a 301-character title and a very large comment
   - voting on your own post and double-clicking vote
   - `/login?next=https://example.com`
   - registering with email delivery misconfigured
   - hammering login from two browsers
   - opening the browser console on each page to look for CSP errors
6. Add screenshots, a demo link and (optionally) a Playwright smoke test.
