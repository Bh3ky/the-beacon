# DEVELOPMENT_TEST_CHECKPOINTS

## Purpose

This file defines the minimum test checkpoints that should be run consistently as implementation progresses through the roadmap phases.

It is not a replacement for [TESTING_STRATEGY.md](/Users/telasi/Developer/the-beacon/docs/TESTING_STRATEGY.md). It is the practical execution checklist to reduce regressions, security mistakes, and silent architecture drift during development.

## Core Rule

At the end of every meaningful implementation slice:

- run the smallest relevant unit and integration tests for the touched domain
- rerun cross-cutting security tests if auth, moderation, ingestion, or feed behavior changed
- do not merge or proceed on broken tests in a previously working critical path

## Always-Critical Checks

These should be rerun frequently throughout development, not just once:

- auth/session flow still works
- CSRF protection still blocks invalid mutating requests
- role enforcement still blocks unauthorized moderation/admin actions
- vote aggregation stays correct
- feed ordering stays stable
- duplicate URL protection still works
- moderation actions still create audit records
- ingestion never bypasses review-first launch policy
- jobs remain out of the main `top` feed

## Phase Checkpoints

### Phase 1 — Project Foundation

Run:

- app boot checks for `apps/web`, `apps/api`, and `apps/worker`
- config-loading tests
- health endpoint test
- local Postgres connectivity check
- local Redis connectivity check

Exit criteria:

- web boots
- API boots
- worker boots
- environment variables load correctly

### Phase 2 — Database and Core Models

Run:

- migration up/down checks
- schema integrity tests
- enum and constraint tests
- foreign key tests
- uniqueness tests for votes, usernames, emails, and dedupe-sensitive fields

Focus:

- `user_sessions`
- `flags.reason_code`
- ingestion lifecycle enum
- source status enum
- URL dedupe constraints

Exit criteria:

- migrations apply cleanly
- schema matches docs
- critical constraints fail correctly on bad data

### Phase 3 — Core API

Run:

- auth endpoint integration tests
- session-cookie tests
- CSRF integration tests
- origin-validation tests
- post creation tests
- comment creation tests
- post vote and comment vote tests
- feed endpoint tests for `top`, `new`, and `jobs`
- permission tests for protected routes

Security-critical regressions to catch:

- missing `HttpOnly` / `Secure` / `SameSite` cookie settings
- mutating requests succeeding without CSRF
- unauthorized users reaching protected routes

Exit criteria:

- core loop works through API only
- auth security contract holds
- feed routes return correct shapes and permissions

### Phase 4 — Frontend Core

Run:

- page render tests for `/`, `/new`, `/jobs`, `/post/[id]/[slug]`, `/user/[username]`
- submission flow tests
- voting UI tests
- comment thread rendering tests
- session bootstrap tests
- CSRF bootstrap and interceptor tests
- basic mobile responsiveness manual checks

Focus:

- frontend sends credentials on session-authenticated requests
- mutating requests attach CSRF token correctly
- jobs surface is visible
- post page route matches canonical slug-aware path

Exit criteria:

- users can browse, authenticate, submit, vote, and comment from the UI
- CSRF/session behavior still works end-to-end

### Phase 5 — Ranking System

Run:

- ranking unit tests
- feed ordering integration tests
- tie-breaker tests
- category feed tests
- jobs feed separation tests
- rank refresh trigger tests

Must verify:

- raw vote counts only in v1
- no weighted voting in `rank_score`
- jobs excluded from main `top`
- jobs feed remains recency-first
- hidden/removed content excluded

Exit criteria:

- feed ordering matches `RANKING_SYSTEM.md`
- ranking behavior is deterministic enough to trust

### Phase 6 — Worker System

Run:

- scheduled job execution tests
- idempotency tests
- duplicate-execution control tests
- worker failure and retry tests
- cache refresh tests
- stale job cleanup tests
- observability/log emission checks

Focus:

- ranking refresh jobs
- feed snapshot refresh
- reconcile counters
- expire job posts

Exit criteria:

- worker jobs run predictably
- failures are visible
- duplicate work is controlled

### Phase 7 — Moderation

Run:

- flag creation tests
- moderation workflow integration tests
- moderation permission tests
- audit log tests
- user suspension/ban tests
- feed exclusion tests for moderated content

Must verify:

- non-moderators cannot trigger moderation actions
- moderation actions create audit records
- banned/suspended users lose intended capabilities
- flagged content flow works end-to-end

Exit criteria:

- moderation is safe, auditable, and usable during MVP testing

### Phase 8 — Ingestion Pipeline

Run:

- feed parsing tests
- normalization tests
- dedupe tests
- ingestion lifecycle tests
- source status handling tests
- moderation-gating tests
- publish-to-post-domain tests
- source failure visibility tests

Must verify:

- all sources are review-first at MVP launch
- no source auto-publishes
- duplicates are blocked across sources
- ingestion items only become posts through the post-domain path
- published ingested posts obey normal ranking rules

Exit criteria:

- ingestion populates content safely
- review-first policy holds
- failures do not silently corrupt the pipeline

### Phase 9 — Production Readiness

Run:

- full unit suite
- full integration suite
- end-to-end suite
- security regression suite
- smoke tests in staging
- backup/restore verification where practical
- deployment smoke tests for web, API, and worker

Must verify:

- auth/session security still holds in deployed environments
- CORS and cross-origin cookie behavior work in staging
- moderation logging works in staging
- ingestion sanitization works in staging
- monitoring and alerts are live

Exit criteria:

- staging behaves like production expectations
- launch checklist items are actually verified, not assumed

## Cross-Cutting Regression Suite

After any change touching auth, ranking, moderation, ingestion, feeds, or worker logic, rerun at least:

- auth/session and CSRF tests
- vote aggregation tests
- `GET /feeds/top` ordering tests
- jobs feed tests
- moderation workflow tests
- dedupe tests
- ingestion review-path tests

## Manual Checks That Still Matter

Even with automated coverage, keep doing these:

- login/logout in browser
- post submission from UI
- voting from UI
- comment reply rendering
- moderator removes flagged content
- ingestion item review and approval
- mobile spot-check on key pages

## Stop-Ship Failures

Do not move forward if any of these regress:

- auth bypass
- CSRF bypass
- unauthorized moderation/admin access
- vote count corruption
- jobs appearing in main `top` feed
- duplicate URLs getting through
- ingestion bypassing review-first launch policy
- moderation actions missing audit records
- worker failures becoming silent

## Usage

Use this file as the recurring implementation checklist during development.

When a roadmap phase begins:

1. identify the phase checkpoint section
2. run the minimum relevant tests as features land
3. rerun the cross-cutting regression suite before considering the phase stable
