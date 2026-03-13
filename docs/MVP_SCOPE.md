# MVP_SCOPE.md

## Project
**Working name:** RiftHub  
**System type:** Community-ranked discovery and discussion platform for African tech

---

# 1. Purpose

This document defines the **Minimum Viable Product (MVP)** scope for the platform.

The goal of the MVP is to:

- launch quickly
- validate community demand
- seed meaningful discussion
- test ranking and ingestion quality
- avoid building unnecessary complexity

The MVP must prioritize **signal and usability**, not feature completeness.

The core question the MVP must answer is:

> Will African tech operators actually use this platform to discover and discuss ecosystem developments?

---

# 2. MVP Success Criteria

The MVP is successful if it demonstrates:

### 1. Content discovery value

Users regularly visit the platform to discover:

- startup launches
- funding announcements
- ecosystem news
- engineering insights

---

### 2. Active discussion

Users are willing to:

- comment
- discuss
- debate ecosystem topics

---

### 3. Community ranking works

Voting should produce feeds where:

- high-value posts rise
- low-value posts sink

---

### 4. Ingestion prevents empty feeds

Automated ingestion ensures the site never looks inactive.

---

# 3. MVP Product Surfaces

The MVP should include the following primary surfaces.

---

# 3.1 Homepage Feed

The homepage shows the **Top feed**.

This is the primary entry point.

Features:

- ranked posts
- voting
- comment counts
- submission metadata
- category badges

Example item:

▲ 87 Flutterwave launches new cross-border payments API
techcabal.com
4 hours ago | 23 comments


---

# 3.2 "New" Feed

Shows posts ordered by creation time.

Purpose:

- ensure transparency
- allow discovery of new submissions before ranking settles

---

# 3.3 Jobs Feed

Jobs should be visible in the MVP through a dedicated jobs surface.

Purpose:

- separate hiring content from the main `top` feed
- keep job discovery useful without distorting story ranking

Jobs feed behavior:

- ordered primarily by freshness
- excludes expired jobs
- separate from the main `top` feed

---

# 3.4 Post Detail Page

Each post has its own page.

Contains:

- post title
- link preview
- metadata
- comment thread
- voting
- comment submission

---

# 3.5 Comment Threads

Users can comment on posts.

Features:

- threaded replies
- vote on comments
- collapse threads
- basic nesting limit

---

# 3.6 Post Submission

Users can submit posts.

Supported types:

| Type | Example |
|-----|-----|
link | tech article |
text | discussion prompt |
job | job listing |

`show` remains a category, not a post type. A showcase post can therefore be submitted as `link` or `text` with category `show`.

Submission includes:

- title
- URL (optional)
- post type
- category
- text body (optional)

---

# 3.7 Voting

Users can vote on:

- posts
- comments

Vote behavior:

- upvote
- undo vote

Votes influence ranking score.

---

# 3.8 User Accounts

Basic accounts are required for participation.

Users can:

- register
- login
- submit posts
- vote
- comment
- flag content

Profile page shows:

- username
- join date
- karma
- recent activity

---

# 3.9 Flagging System

Users can flag content.

Flag reasons:

- spam
- abuse
- misinformation
- off_topic
- other

Flags appear in moderator review queue.

---

# 3.10 Moderator Dashboard

Moderators can:

- review flagged content
- remove posts
- remove comments
- suspend users
- ban users

Moderation UI should remain simple in MVP.

---

# 3.11 Ingestion Engine

The system imports posts from approved external sources.

Illustrative examples:

- TechCabal
- TechCrunch Africa
- Rest of World
- company blogs

Ingestion pipeline:

```text
poll sources
→ parse feeds
→ normalize items
→ dedupe
→ moderation review
→ publish or reject
```


This prevents empty feeds.

---

# 4. MVP Categories

The MVP should support a limited category set.

Recommended categories:

| Category | Description |
|---|---|
funding | startup funding rounds |
launch | product launches |
engineering | technical content |
ecosystem | policy, ecosystem insights |
ask | community questions and prompts |
show | builds, launches, and showcase posts |
jobs | job postings |

Categories help organize content but should not overcomplicate ranking.

---

# 5. Ranking System (MVP)

Ranking behavior should be simple, stable, and consistent with `RANKING_SYSTEM.md`.

For MVP:

- use raw vote counts only
- do not enable weighted voting inside `rank_score`
- keep jobs on a separate feed with recency-first logic
- keep job posts out of the main `top` feed

Ranking updates:

- when votes change
- periodically via worker refresh

Feed cache refresh interval:


30–60 seconds


---

# 6. MVP Features (Included)

The following features must exist in the MVP.

| Feature | Status |
|---|---|
homepage feed | required |
new feed | required |
post pages | required |
comments | required |
voting | required |
user accounts | required |
post submission | required |
flagging | required |
moderator dashboard | required |
jobs feed | required |
RSS ingestion | required |

These form the **core product loop**.

---

# 7. MVP Features (Deferred)

The following features should **not** be built initially.

They add complexity without validating the core idea.

| Feature | Reason |
|---|---|
notifications | unnecessary early |
user following | premature |
private messaging | scope creep |
advanced reputation system | premature |
complex recommendation engine | premature |
full search engine | unnecessary early |
mobile apps | web sufficient |
AI summarization | unnecessary early |

These can be built later if the product proves traction.

---

# 8. MVP Source Ingestion

Initial approved sources may include illustrative examples such as:

Examples:

- TechCabal
- TechCrunch Africa
- Disrupt Africa
- Benjamindada
- Techpoint Africa
- company engineering blogs

Each source will have:

- polling interval
- trust score
- auto-publish flag

At MVP launch, all sources are review-first.

No sources auto-publish at launch.

The actual approved source list still needs to be defined explicitly.

---

# 9. MVP Anti-Spam Measures

Minimal protections should exist.

Examples:

- account required to vote
- rate limit submissions
- rate limit comments
- URL dedupe
- domain blocking

More sophisticated spam systems can come later.

---

# 10. MVP Analytics

Basic metrics should be tracked.

Examples:

- daily active users
- posts per day
- comments per post
- votes per post
- ingestion success rate

These help determine if the platform is gaining traction.

---

# 11. MVP Launch Strategy

A silent launch is recommended.

Steps:

1. deploy platform
2. seed with approved review-first ingestion sources
3. invite a small group of early users

Example early users:

- African founders
- engineers
- startup operators
- tech journalists

Initial user count target:


50–200 early users


---

# 12. MVP Growth Loops

The platform should grow through:

### 1. discoverability

Users discover content faster than on Twitter or newsletters.

---

### 2. discussion quality

Meaningful discussions attract repeat users.

---

### 3. ecosystem participation

Founders share launches and insights.

---

### 4. ingestion pipeline

The site never appears inactive.

---

# 13. MVP Risks

The biggest risks are:

### Empty community

Without active users, discussion may be weak.

Mitigation:

- invite founders and operators early

---

### Spam

Open submission systems attract spam.

Mitigation:

- moderation
- rate limits

---

### Poor ranking

If ranking fails, feed quality drops.

Mitigation:

- tune gravity
- add domain trust modifiers

---

# 14. MVP Timeline

Suggested development timeline.

| Phase | Work |
|---|---|
week 1–2 | backend core |
week 2–3 | frontend feed and posts |
week 3–4 | voting and comments |
week 4–5 | ingestion pipeline |
week 5–6 | moderation dashboard |
week 6 | staging and launch |

Total timeline:


~6 weeks


for a working MVP.

---

# 15. Summary

The MVP focuses on a single core loop:


discover → vote → discuss → submit


Supported by:

- ranking system
- ingestion pipeline
- moderation

The MVP deliberately avoids unnecessary complexity.

If the core loop succeeds, the platform can evolve into a larger ecosystem intelligenc
