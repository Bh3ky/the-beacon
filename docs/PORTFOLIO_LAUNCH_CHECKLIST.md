# RiftHub Launch Checklist

## Positioning

RiftHub as of now is a **feature-rich MVP** for a community-ranked African tech discovery platform. The current goal is:

- deploy a stable demo


Core demo loop:

```text
discover -> vote -> discuss -> submit
```

## Current State

### Completed

- [x] FastAPI application entrypoint and health endpoint
- [x] Versioned API routes under `/v1`
- [x] User registration, verification, login, logout, and current-user session
- [x] Session cookies and CSRF checks for authenticated mutations
- [x] Auth rate limiting with memory and Redis backends
- [x] Post creation and post detail API
- [x] Feeds for top, new, jobs, ask, and show
- [x] Post voting and undo-vote behavior
- [x] Comment creation and threaded comment reads
- [x] Comment voting and undo-vote behavior
- [x] Flagging system
- [x] Moderator/admin APIs for flags, post/comment removal, user suspension/ban, ingestion review, and source health
- [x] Ranking refresh backend logic
- [x] Feed snapshot backend logic
- [x] RSS ingestion backend logic
- [x] Job expiry backend logic
- [x] Worker scheduler for recurring background jobs
- [x] Next.js pages for home, new, ask, show, jobs, post detail, submit, login, register, verify, and moderation
- [x] Frontend API proxy for browser-origin API calls
- [x] Seed scripts for development feed and approved sources
- [x] Alembic migrations for the current schema

### Verified

- [x] Web production build passes with `npm run --workspace @rifthub/web build`
- [x] API tests pass with `RIFTHUB_REDIS_URL=` set for the test run
- [x] Worker tests pass with `uv run --package rifthub-worker pytest apps/worker/tests`

## Must Fix Before Deployment

### Documentation

- [ ] Rewrite `README.md` so it matches the actual project.
- [ ] Replace the stale clone path that still references `the-beacon`.
- [x] Update Python requirement from `3.11+` to the package requirement, currently `>=3.12`.
- [x] Remove Celery from the listed stack unless it is actually added.
- [ ] Describe the worker as the current custom async scheduler.
- [ ] Replace the old unchecked roadmap list with a realistic MVP status section.
- [ ] Remove or clearly mark unimplemented features such as profiles, search, topic tags, newsletter, reputation, and AI recommendations.
- [ ] Add a clear local setup flow for web, API, worker, Postgres, Redis, migrations, and seed data.

### Environment Configuration

- [ ] Expand `.env.example` with every production-relevant setting used by `Settings`.
- [ ] Add `RIFTHUB_APP_SECRET`.
- [ ] Add `RIFTHUB_ALLOWED_ORIGINS`.
- [ ] Add `RIFTHUB_FRONTEND_BASE_URL`.
- [ ] Add `RIFTHUB_VERIFICATION_DELIVERY_MODE`.
- [ ] Add SMTP settings or Resend settings, depending on the chosen email provider.
- [ ] Add `RIFTHUB_RESEND_API_KEY` if Resend is used.
- [ ] Add `RIFTHUB_INGESTION_SYSTEM_USERNAME`.
- [ ] Add `RIFTHUB_INGESTION_SYSTEM_EMAIL`.
- [ ] Make sure placeholder values are obviously fake and safe to commit.
- [ ] Keep real `.env` files ignored.

### Test Reliability

- [ ] Fix the config test isolation issue where local `RIFTHUB_REDIS_URL` can break the default-settings test.
- [ ] Ensure `npm run api:test` passes without requiring manual env cleanup.
- [ ] Add a root-level verification command if useful, for example `test` or `check`, that runs web build, API tests, and worker tests.

### Deployment Decisions

- [ ] Choose the deployment target for the web app.
- [ ] Choose the deployment target for the API.
- [ ] Choose where the worker will run.
- [ ] Choose managed Postgres.
- [ ] Choose managed Redis.
- [ ] Decide whether email verification will use SMTP, Resend, or log/noop for the demo.
- [ ] Decide whether the deployed portfolio demo allows open registration or uses seeded demo accounts.

### Production Environment Values

- [ ] Set `RIFTHUB_ENV=production`.
- [ ] Set `RIFTHUB_DATABASE_URL`.
- [ ] Set `RIFTHUB_MIGRATION_DATABASE_URL` if migrations use a separate connection.
- [ ] Set `RIFTHUB_REDIS_URL`.
- [ ] Set `RIFTHUB_RATE_LIMIT_BACKEND=redis`.
- [ ] Set a strong `RIFTHUB_APP_SECRET`.
- [ ] Set `RIFTHUB_ALLOWED_ORIGINS` to the deployed web origin.
- [ ] Set `RIFTHUB_FRONTEND_BASE_URL` to the deployed web URL.
- [ ] Set `RIFTHUB_API_BASE_URL` for the web deployment.
- [ ] Set trusted proxy IP behavior for the API host.
- [ ] Configure verification email delivery.

### Database And Data

- [ ] Provision the production database.
- [ ] Run Alembic migrations.
- [ ] Seed approved sources.
- [ ] Seed enough initial feed content that the homepage does not look empty.
- [ ] Create an admin user.
- [ ] Create a moderator user if separate from admin.
- [ ] Verify the moderation dashboard with the admin/moderator account.

### Smoke Test The Deployed App

- [ ] Visit the homepage and confirm the top feed loads.
- [ ] Visit new, ask, show, and jobs feeds.
- [ ] Register a user.
- [ ] Verify the user account.
- [ ] Login and logout.
- [ ] Submit a link post.
- [ ] Submit a text/ask post.
- [ ] Submit or seed a job post.
- [ ] Upvote and undo an upvote on a post.
- [ ] Open a post detail page.
- [ ] Add a top-level comment.
- [ ] Add a reply.
- [ ] Upvote and undo an upvote on a comment.
- [ ] Flag a post or comment.
- [ ] Review the flag in moderation.
- [ ] Confirm the worker can refresh scores and feeds.
- [ ] Confirm expired jobs are excluded from the jobs feed.

## Nice To Fix Before Showcase

- [ ] Add a short `docs/DEPLOYMENT.md`.
- [ ] Add screenshots or a GIF to the README.
- [ ] Add a small architecture diagram.
- [ ] Add a “Known limitations” section to the README.
- [ ] Add a “Demo credentials” section if using seeded accounts.
- [ ] Add linting for the frontend.
- [ ] Add a frontend smoke test or Playwright check for the main pages.
- [ ] Make the Next API proxy support `PUT` and `PATCH` for future API routes.
- [ ] Review the post/comment thread UX for mobile.
- [ ] Add explicit empty states for unseeded feeds that still look intentional.

## Known Gaps To Be Honest About

- [ ] Public user profile pages are not implemented.
- [ ] Search is not implemented.
- [ ] Topic tags are not implemented as a full product surface.
- [ ] Newsletter/digest functionality is not implemented.
- [ ] AI recommendations are not implemented.
- [ ] Full reputation mechanics are not implemented beyond existing user/post/comment counters and karma-like fields.
- [ ] Comment collapse behavior may not be implemented even though threaded comments exist.
- [ ] One migration has a no-op downgrade for a PostgreSQL enum value, so rollback is not fully reversible there.

## Recommended Launch Order

1. Fix README and `.env.example`.
2. Fix config test isolation.
3. Add deployment notes.
4. Provision Postgres and Redis.
5. Deploy API.
6. Run migrations.
7. Deploy worker.
8. Deploy web.
9. Seed sources and starter content.
10. Create admin/moderator account.
11. Run the smoke test checklist.
12. Add final portfolio copy and screenshots.

### Q

> RiftHub is a feature-rich MVP for discovering, ranking, and discussing African tech ecosystem stories. It includes a Next.js frontend, FastAPI backend, PostgreSQL persistence, Redis-backed rate limiting, background ingestion/ranking workers, authentication, voting, threaded discussions, and moderation tooling.


