# TESTING_STRATEGY.md

## Project
**Working name:** RiftHub  
**System type:** Community-ranked discovery and discussion platform for African tech

---

# 1. Purpose

This document defines the testing strategy for the platform.

Testing ensures that:

- core features behave correctly
- ranking logic produces stable results
- ingestion pipelines remain reliable
- moderation tools function safely
- regressions are detected early

The platform contains several components that are particularly sensitive to bugs:

- ranking algorithms
- ingestion pipelines
- vote aggregation
- moderation actions

Testing should focus heavily on these areas.

---

# 2. Testing Philosophy

The testing strategy follows these principles.

## 2.1 Test the most critical systems first

Not all parts of the system require equal testing coverage.

Highest priority areas:

- ranking
- votes
- posts
- comments
- ingestion pipeline
- moderation actions

Lower priority areas:

- simple UI layout
- static pages
- styling

---

## 2.2 Automate where possible

Tests should run automatically in CI.

Automation ensures that:

- new code does not break existing behavior
- developers receive fast feedback
- releases are safer

---

## 2.3 Focus on behavior, not implementation

Tests should validate system behavior rather than internal implementation details.

Example:

Good test:


post with more votes ranks higher


Bad test:


function calculate_score returns specific floating value


Tests should validate **observable outcomes**.

---

# 3. Testing Levels

The platform should include three primary testing levels.

| Test Type | Purpose |
|---|---|
Unit tests | verify small pieces of logic |
Integration tests | verify system components interact correctly |
End-to-end tests | simulate real user workflows |

Each level serves a different purpose.

---

# 4. Unit Tests

Unit tests verify small pieces of code in isolation.

These tests should run quickly and frequently.

---

# 4.1 Ranking Logic Tests

Ranking determines feed quality, so it must be heavily tested.

Tests should verify:

- newer posts rank higher than old posts with equal votes
- higher vote counts increase ranking
- time decay reduces score over time
- category modifiers behave correctly
- domain trust modifiers behave correctly
- jobs do not appear in the main `top` feed
- jobs feed ordering remains separate and recency-first
- ranking behavior uses raw vote counts only in v1

Example test:


post_A: 50 votes, 10 hours old
post_B: 40 votes, 1 hour old

expected → post_B ranks higher


---

# 4.2 Vote Aggregation Tests

Vote logic must remain correct.

Tests should verify:

- one vote per user
- vote toggle behavior
- vote removal updates aggregates
- race conditions do not corrupt counts

Example:


user votes
vote count increases

user removes vote
vote count decreases


---

# 4.3 Post Validation Tests

Post creation rules should be tested.

Examples:

- title required
- URL normalization works
- duplicate link detection works
- text posts allowed without URL

---

# 4.4 Comment Logic Tests

Comment behavior should be tested.

Examples:

- parent-child relationships
- nesting limits
- comment editing rules
- comment deletion behavior

---

# 4.5 Moderation Logic Tests

Moderation actions must behave safely.

Tests should verify:

- moderators can remove posts
- moderators can remove comments
- moderators cannot escalate privileges
- banned users cannot submit content
- moderation actions create audit records

---

# 4.6 Auth and Session Tests

Authentication behavior is security-critical.

Tests should verify:

- login sets the session cookie correctly
- logout invalidates the session server-side
- protected routes reject missing sessions
- mutating routes reject missing or invalid CSRF tokens
- origin checks block untrusted state-changing requests

---

# 5. Integration Tests

Integration tests verify interaction between multiple components.

These tests typically involve:

- database
- API routes
- service logic

---

# 5.1 API Endpoint Tests

Important API endpoints should have integration tests.

Examples:

| Endpoint | Test |
|---|---|
POST /posts | post creation works |
POST /posts/{post_id}/comments | comment creation works |
POST /posts/{post_id}/vote | post vote recorded correctly |
POST /comments/{comment_id}/vote | comment vote recorded correctly |
GET /feeds/top | feed ordering correct |
GET /auth/me | current session resolves correctly |

Tests should verify both:

- successful responses
- error conditions

---

# 5.2 Database Integrity Tests

Database constraints should be verified.

Examples:

- unique vote per user per target
- foreign key relationships
- cascade deletes behave correctly

---

# 5.3 Feed Generation Tests

Feed generation is critical.

Tests should verify:

- ranking order
- hidden posts excluded
- removed posts excluded
- pagination behaves correctly
- job posts excluded from `top`
- jobs feed uses its own eligibility and ordering rules

---

# 5.4 Moderation Workflow Tests

Moderation workflow should be tested.

Examples:


user flags post
moderator reviews flag
moderator removes post
post disappears from feeds
moderation action record is created


---

# 6. Ingestion Pipeline Tests

The ingestion system is complex and must be tested carefully.

---

# 6.1 Feed Parsing Tests

Test parsing of:

- RSS feeds
- Atom feeds
- JSON feeds

Tests should verify:

- titles parsed correctly
- URLs extracted
- timestamps parsed correctly

---

# 6.2 Normalization Tests

URL normalization must be tested.

Example:


https://example.com/article?utm_source=twitter


Normalized to:


https://example.com/article


This prevents duplicate posts.

---

# 6.3 Deduplication Tests

Deduplication must detect:

- identical URLs
- equivalent canonical URLs

Example:


site.com/article
www.site.com/article


Should be treated as duplicates.

---

# 6.4 Source Trust Tests

Tests should verify behavior when:

- trusted source publishes item
- low-trust source publishes item

Expected outcomes:

- both sources enter review-first ingestion flow at MVP launch
- source status and trust still affect operator review priority and future policy decisions

---

# 7. End-to-End Tests

End-to-end tests simulate real user behavior.

These tests verify complete workflows.

---

# 7.1 User Registration Flow

Test:


user registers
user logs in
user session is established
user accesses authenticated features


---

# 7.2 Post Submission Flow

Test:


user submits post
post appears in new feed
users vote
post rises in ranking


---

# 7.3 Comment Interaction

Test:


user posts comment
another user replies
thread structure maintained


---

# 7.4 Moderation Flow

Test:


user flags content
moderator removes content
content disappears from feed


---

# 7.5 Ingestion Flow

Test:


RSS source publishes article
worker polls source
item ingested
item enters review queue
moderator approves item
item appears in feed


---

# 8. Test Data Strategy

Tests require consistent data.

Recommended approach:

- use factory fixtures
- generate test posts
- generate test users
- generate test votes

Factories should create realistic test data.

Example:


create_user()
create_post()
create_comment()
create_vote()


---

# 9. CI Testing Pipeline

Tests should run automatically during CI.

Suggested pipeline steps:


install dependencies
run lint
run unit tests
run integration tests
build frontend


If tests fail, the build should fail.

---

# 10. Performance Testing

Performance testing is useful for feed queries.

Key scenarios:

- feed query with thousands of posts
- comment thread with deep nesting
- ingestion processing bursts

Performance testing ensures the system remains responsive.

---

# 11. Manual Testing

Some testing should remain manual.

Examples:

- UI usability
- moderation dashboard experience
- mobile responsiveness
- onboarding flow

Manual testing helps catch issues automated tests miss.

---

# 12. Regression Testing

Whenever major systems change, regression tests should run.

High-risk changes include:

- ranking algorithm updates
- vote aggregation changes
- ingestion pipeline modifications
- moderation logic changes

Regression tests ensure existing behavior is preserved.

---

# 13. Test Coverage Goals

Coverage targets should focus on critical logic.

Recommended targets:

| Area | Target Coverage |
|---|---|
ranking | high |
votes | high |
posts | high |
comments | medium |
ingestion | high |
moderation | high |
UI | low to medium |

Perfect coverage is not required.

Meaningful coverage is.

---

# 14. Test Environment

Tests should run in isolated environments.

Components used:

- temporary database
- test Redis instance
- mocked external sources

Isolation prevents test interference.

---

# 15. Testing Tools

Recommended tools:

Backend:

- pytest
- pytest-asyncio
- factory-boy

Frontend:

- Playwright
- React Testing Library

CI:

- GitHub Actions

---

# 16. Testing Checklist

Before launch confirm:

- ranking tests pass
- vote logic tests pass
- auth/session and CSRF tests pass
- feed generation tests pass
- ingestion tests pass
- moderation tests pass
- key user workflows verified

Testing should provide confidence that the system behaves predictably.

---

# 17. Summary

Testing ensures the platform remains reliable as it evolves.

The most important systems to test are:

- ranking
- votes
- ingestion
- moderation
- feed generation

By combining:

- unit tests
- integration tests
- end-to-end tests

the platform can evolve safely without breaking core functionality.
