# RANKING_SYSTEM.md

## Project
**Working name:** RiftHub  
**System type:** Community-ranked discussion and discovery platform for African tech

---

# 1. Purpose

This document defines how content is ranked across the platform.

The ranking system is the core product engine. It determines:

- what appears on the homepage
- how long posts remain visible
- how user votes affect visibility
- how comments are ordered
- how low-quality or manipulative content is suppressed
- how ingested content competes with user-submitted content

This is not a generic sorting feature. It is the mechanism that converts raw submissions into a usable signal layer for the African tech ecosystem.

---

# 2. Ranking Philosophy

## 2.1 Product goal

The ranking system should maximize **signal**, not raw engagement.

The platform should reward:

- genuinely relevant stories
- timely ecosystem developments
- thoughtful discussion
- useful launches
- high-trust submissions
- substantive community participation

It should suppress:

- spam
- low-effort self-promotion
- duplicate stories
- stale content
- brigaded or manipulated posts
- low-trust domains with weak engagement

---

## 2.2 Why this matters

Feed products fail when ranking is naive.

If ranking is too simple:

- early spam gets through
- low-quality content farms the feed
- duplicate stories dominate
- users stop trusting the homepage

If ranking is too complex:

- behavior becomes opaque
- debugging becomes hard
- moderation becomes inconsistent
- small-community dynamics break

The system therefore needs to be:

- understandable
- tunable
- resistant to abuse
- lightweight enough for MVP
- extensible later

---

# 3. Core Ranking Surfaces

The platform does not have one universal ranking mode. Different surfaces have different ordering logic.

## 3.1 Feed surfaces

| Feed | Ranking mode |
|---|---|
| `top` | hot score with time decay |
| `new` | reverse chronological |
| `ask` | hot score filtered to `category = ask` |
| `show` | hot score filtered to `category = show` |
| `jobs` | recency-first with optional light trust weighting |
| future category feeds | hot score within category |

---

## 3.2 Comment surfaces

| Surface | Ranking mode |
|---|---|
| post comment tree | thread-first with score-aware sibling ordering |
| future “top comments” view | comment hot score |

---

# 4. Ranking Objectives

The ranking system should satisfy the following objectives.

## 4.1 Freshness

New stories should have a chance to appear before they accumulate many votes.

## 4.2 Stability

Good stories should remain visible long enough to gather discussion.

## 4.3 Abuse resistance

Single users or low-quality domains should not trivially push content up the feed.

## 4.4 Small-ecosystem fit

The African tech ecosystem generates less total story volume than a global tech platform. Ranking must therefore decay more slowly than Hacker News-style systems optimized for massive submission volume.

## 4.5 Editorial neutrality with light intervention

The platform should remain community-ranked, but it may apply modest trust and category adjustments where they materially improve signal quality.

---

# 5. Core Ranking Concepts

The ranking model is built from a few distinct layers.

## 5.1 Raw engagement

The simplest interaction layer:

- upvotes
- downvotes if enabled later
- comments
- saves/bookmarks later if added

## 5.2 Weighted engagement

Votes may carry different strength depending on user trust/reputation.

## 5.3 Time decay

Older posts should gradually lose ranking strength.

## 5.4 Trust adjustments

Source trust and limited moderation heuristics may slightly affect visibility.

## 5.5 Feed-specific filtering

A post might be valid globally but excluded from a specific feed.

Example:

- jobs should not dominate `top`
- removed/hidden posts should never rank
- expired jobs should disappear from jobs feed

---

# 6. Baseline Data Inputs

The ranking engine assumes access to the following fields from the database model.

## 6.1 Post-level inputs

- `post.id`
- `post.post_type`
- `post.category`
- `post.status`
- `post.submitted_at`
- `post.upvote_count`
- `post.downvote_count`
- `post.comment_count`
- `post.score`
- `post.rank_score`
- `post.last_commented_at`
- `post.job_expires_at`
- `post.is_ingested`
- `post.domain_id`

## 6.2 Domain-level inputs

- `domain.trust_score`
- `domain.is_blocked`

## 6.3 User-level inputs for weighted voting

- `user.karma`
- `user.status`
- account age
- moderation history if later added

---

# 7. Initial Recommended Model

The v1 ranking system should be intentionally simple but strong enough to support growth.

## 7.1 Recommended base formula

For the `top` feed:

```text
base_vote_score = weighted_upvotes - weighted_downvotes + 1
rank_score = base_vote_score / ((age_hours + 3) ^ gravity)
```

Where:

- `age_hours` = hours since `submitted_at`
- `gravity` = ranking decay constant
- `+1` prevents zero-score dead-start behavior

## 7.2 Recommended initial gravity

```text
gravity = 1.4
```

**Why not use a stronger Hacker News-style gravity?**

A stronger gravity like `1.8` is better suited to high-volume ecosystems with constant submission pressure. This platform will have lower content velocity, so a lower gravity is appropriate.

A lower gravity ensures:

- good stories remain visible longer
- the homepage does not feel empty
- slower discussions still matter
- quality content from smaller markets does not disappear too quickly

## 7.3 Age buffer

The `+3` in the denominator is intentional.

```text
(age_hours + 3)
```

This avoids severe early volatility and gives new posts a short runway to gather signal before being crushed by time decay.

# 8. Weighted Voting

## 8.1 Why weighted voting exists

In a small community, raw one-user-one-vote systems are vulnerable to:

- sockpuppets
- brigading
- spam accounts
- new low-quality accounts manipulating feed movement

Weighted voting gives trusted contributors slightly more influence without turning the system into an oligarchy.

## 8.2 Initial recommendation

Use a lightweight vote weight, not aggressive multipliers.

Recommended conceptual model:

```text
vote_weight = min(1.5, 1 + log10(user_karma + 1) * 0.2)
```

Interpretation:

- new users still count
- established users count slightly more
- the ceiling prevents runaway elite amplification

## 8.3 Simpler MVP alternative

If you want a simpler v1 launch, start with:

```text
weighted_upvotes = upvote_count
weighted_downvotes = downvote_count
```

Then enable weighted voting later.

This is acceptable if:

- moderation is active
- registrations are controlled enough
- anti-spam gates exist
- the platform is still small and curated

## 8.4 Recommended practical choice

For v1:

- store raw votes normally
- compute score from raw counts
- optionally introduce weighting only inside `rank_score`, not in displayed vote totals

This preserves transparency:

- visible vote counts remain intuitive
- ranking gets modest trust-awareness
- users do not see unexplained vote math

# 9. Comment Influence on Post Ranking

## 9.1 Should comments influence top-feed ranking?

Yes, but lightly.

A post with active, substantive discussion is often more important than a post with passive voting only. However, comment count should not overpower votes, or controversy bait will dominate.

## 9.2 Recommended light comment boost

Use a bounded comment factor such as:

```text
comment_factor = 1 + min(0.25, log2(comment_count + 1) * 0.05)
```

Then:

```text
rank_score = (base_vote_score * comment_factor) / ((age_hours + 3) ^ gravity)
```

This means:

- early comments help
- huge threads do not explode rank infinitely
- discussion helps, but does not replace voting

## 9.3 Why the cap matters

Without a cap, debate-heavy or flamebait posts can dominate disproportionately. The cap keeps comments relevant but secondary.

# 10. Category Adjustments

## 10.1 Principle

Category boosts should be used sparingly. The platform should not feel editorially rigged.

However, some categories are structurally more valuable to the ecosystem and may deserve a small uplift.

## 10.2 Recommended initial category multipliers

```text
funding      = 1.10
launch       = 1.10
policy       = 1.05
engineering  = 1.05
ecosystem    = 1.00
opinion      = 1.00
ask          = 1.00
show         = 1.00
jobs         = separate feed logic
```

Then:

```text
adjusted_rank_score = rank_score * category_multiplier
```

## 10.3 Guidance

Do not exceed small boosts in v1. Large category multipliers quickly undermine community trust.

If you want stronger editorial control, use:

- pinned posts
- moderator features
- curated digest surfaces

Do not use heavy hidden ranking inflation.

# 11. Domain Trust Adjustments

## 11.1 Why domain trust matters

Not all sources are equal.

A platform like this will eventually attract:

- trusted publishers
- startup blogs
- founder self-promotion
- SEO farms
- spam domains

Domain trust gives the system a light defensive layer.

## 11.2 Recommended domain modifier

```text
domain_modifier = clamp(domain.trust_score, 0.85, 1.05)
```

Where:

- low-trust sources can be lightly penalized
- trusted sources can be lightly boosted
- blocked domains are excluded entirely

Then:

```text
final_rank_score = adjusted_rank_score * domain_modifier
```

## 11.3 Trust score interpretation

Example conceptual ranges:

| Trust score | Meaning |
| --- | --- |
| `0.85` | suspicious / low trust |
| `1.00` | neutral |
| `1.05` | trusted source |

This should remain subtle. Domain trust is not a replacement for moderation.

# 12. Final Top Feed Formula

A practical v1 formula combining the above:

```text
base_vote_score = weighted_upvotes - weighted_downvotes + 1
comment_factor = 1 + min(0.25, log2(comment_count + 1) * 0.05)
hot_score = (base_vote_score * comment_factor) / ((age_hours + 3) ^ gravity)
category_adjusted_score = hot_score * category_multiplier
final_rank_score = category_adjusted_score * domain_modifier
```

Where:

- `gravity = 1.4`
- `category_multiplier` usually ranges `1.00` to `1.10`
- `domain_modifier` usually ranges `0.85` to `1.05`

This `final_rank_score` is what should typically be persisted into `posts.rank_score`.

# 13. Feed-Specific Ranking Rules

## 13.1 Top feed

**Eligibility**

A post is eligible for `top` only if:

- `status = active`
- it is not blocked by moderation
- if `post_type = job`, it is either excluded entirely or included only under special policy
- if a job post is included, it must not be expired

**Ordering**

- order by `rank_score desc`
- use a deterministic tie-breaker such as `submitted_at desc`, then `id desc`

## 13.2 New feed

**Eligibility**

Same as above, except there is no hot-score requirement.

**Ordering**

```text
submitted_at desc
```

Tie-breakers:

- `id desc`

No vote weighting, category boost, or domain modifier is needed beyond hard blocking logic.

## 13.3 Ask feed

**Eligibility**

- `status = active`
- `category = ask`

**Ordering**

Use the same hot-score model as `top`, but within category scope.

## 13.4 Show feed

**Eligibility**

- `status = active`
- `category = show`

**Ordering**

Use the same hot-score model as `top`, but within category scope.

## 13.5 Jobs feed

Jobs should behave differently.

**Why**

Users generally want jobs by freshness and validity, not community debate.

**Recommended jobs ordering**

```text
job_rank = recency_score * trust_modifier
```

**Eligibility**

- `post_type = job`
- `category = jobs`
- `status = active`
- `job_expires_at` is null or in the future

Practical implementation:

- order primarily by `submitted_at desc`
- optionally apply light domain or company trust weighting
- optionally boost jobs with valid metadata completeness later

Do not use the main hot-score formula for jobs in v1.

# 14. Comment Ranking

Comments require separate treatment from posts.

## 14.1 Goals

Comment ranking should:

- preserve thread structure
- reward useful replies
- suppress low-value noise
- avoid making deep threads unreadable

## 14.2 Recommended storage

Each comment stores:

- raw score
- rank score
- depth
- parent comment ID

The frontend reconstructs the tree from flat API output.

## 14.3 Comment score formula

A simple v1 formula:

```text
comment_base_score = upvotes - downvotes + 1
comment_rank_score = comment_base_score / ((age_hours + 2) ^ 1.2)
```

This gives:

- some freshness bias
- enough persistence for good comments
- less aggressive decay than a pure recency sort

## 14.4 How comments should be displayed

Recommended display rule:

- preserve thread structure first
- sort sibling comments by `comment_rank_score desc`
- do not flatten the whole tree by score globally

This avoids destroying conversational coherence.

## 14.5 Collapsing rules

Low-quality comments may be collapsed in the UI if:

- score is below threshold
- status is `hidden` or `removed`
- author is banned or suspended and comment is policy-suppressed

This is a UI concern, but ranking should provide the inputs.

# 15. Vote Semantics

## 15.1 V1 recommendation

The platform should launch with:

- upvote-only UI for posts
- upvote-only UI for comments

Even if the schema supports `-1`, public downvotes should remain disabled initially.

## 15.2 Why upvote-only first

Benefits:

- lower toxicity
- simpler social model
- easier explanation to users
- less brigading pressure early
- easier moderation

The ranking engine remains future-compatible with downvotes if needed later.

## 15.3 Moderator or trust-tier downvotes later

If the platform later adds downvotes, there are several controlled paths:

- moderator-only downvotes
- high-trust-user downvotes
- public downvotes with stricter anti-abuse protections

This should not be enabled casually. Downvotes change culture significantly.

# 16. Anti-Abuse Ranking Protections

Ranking alone is not enough. It needs guardrails.

## 16.1 Submission dedupe

Duplicate links should not compete separately.

If `url_normalized` already exists within the repost window:

- reject the submission
- or redirect to the existing post

This prevents vote fragmentation and feed clutter.

## 16.2 Rate limits

The platform should rate-limit:

- post submissions
- voting bursts
- comment bursts
- flag creation

This is not ranking math, but it preserves ranking integrity.

## 16.3 Self-vote policy

Recommended:

- users cannot vote on their own posts or comments

If allowed later, self-votes should not affect ranking.

## 16.4 Low-trust or new-account friction

Possible rules:

- low-account-age votes count only partially
- first submissions may go through stricter checks
- suspicious accounts may be shadow-limited from ranking influence

For v1, keep this light and mostly moderation-driven unless abuse becomes real.

## 16.5 Brigading detection

Not required for first launch, but it should be planned conceptually.

Future signals:

- abnormal voting velocity
- correlated account creation patterns
- shared IP or device heuristics if policy allows
- repeated domain-specific manipulation

If suspicious activity is detected, ranking influence can be dampened or votes held for review.

# 17. Ingested Content and Ranking

## 17.1 Why this matters

The platform will use ingestion to solve the cold-start problem. If ingested content is treated carelessly, it can overwhelm native community behavior.

## 17.2 Recommended principles

Ingested posts should:

- enter the same ranking universe as user posts once published
- be clearly attributable to their source
- not receive unfair hidden boosts simply for being ingested

However, ingestion source trust may influence domain trust or initial eligibility.

## 17.3 Initial rank for ingested posts

Recommended approach:

- publish with normal baseline score
- allow community votes and comments to determine actual rise
- optionally seed a tiny neutral starting score to avoid dead-on-arrival invisibility

For example:

```text
base_vote_score starts at 1
```

This already happens through the `+1` formulation.

## 17.4 Auto-published vs reviewed ingestion

High-trust sources may auto-publish directly into eligible feeds.

Lower-trust sources should be reviewed before publication.

This is a moderation and ingestion policy concern, but it affects what enters the ranking pool.

# 18. Score Recalculation Strategy

The platform needs a reliable method for keeping `rank_score` fresh without excessive computation.

## 18.1 Hybrid strategy

Recommended approach:

**On write**

Recompute or queue recomputation when:

- a post is created
- a vote changes
- a comment is added
- a moderator changes visibility or category
- domain trust changes materially

**Scheduled refresh**

Periodically recompute scores for:

- active top-feed candidate posts
- recent posts within a sliding time window
- heavily active discussion threads

## 18.2 Why not compute everything live on every request?

That approach becomes wasteful and inconsistent under load. Persisting `rank_score` and refreshing it predictably is more practical.

## 18.3 Recommended recalculation windows

For v1, focus recomputation on:

- posts created in the last 72 hours
- posts with active recent comments
- posts currently cached in top feed snapshots

Older posts can be recalculated less frequently.

# 19. Caching and Feed Snapshots

## 19.1 Feed snapshot concept

The homepage and feed pages are hot read paths. Instead of rebuilding rank order from scratch on every request, the system should cache feed snapshots.

A feed snapshot contains:

- ordered post IDs
- optionally pre-hydrated minimal post metadata
- generated timestamp
- pagination cursor metadata if needed

## 19.2 Suggested snapshot TTLs

| Feed | TTL |
| --- | --- |
| `top` | 30 to 120 seconds |
| `new` | 30 seconds |
| `ask` | 60 seconds |
| `show` | 60 seconds |
| `jobs` | 2 to 10 minutes |

This keeps ranking reasonably fresh without wasting compute.

## 19.3 Cache invalidation triggers

Invalidate or refresh affected snapshots when:

- a new eligible post is created
- a vote changes on an eligible post
- a comment is added to an eligible post
- moderation visibility changes
- category changes
- a domain becomes blocked or unblocked

# 20. Tie-Breaking Rules

When two posts have equal `rank_score`, deterministic tie-breaks are required.

**Recommended tie-break order**

- `submitted_at desc`
- `comment_count desc`
- `id desc`

This ensures stable ordering and avoids jitter.

For comments, sibling tie-break order can be:

- `comment_rank_score desc`
- `created_at asc` or `created_at desc` depending on product preference
- `id desc`

# 21. Ranking Configuration

The ranking system should be partly configuration-driven, not entirely hardcoded.

## 21.1 Configurable parameters

These should be easy to change:

- gravity
- age buffer (`+3`)
- comment factor cap
- category multipliers
- domain modifier bounds
- repost window length
- job expiry defaults
- trust thresholds for auto-publish eligibility

## 21.2 Why configuration matters

This platform will need tuning after real usage begins. You do not want to redeploy deep logic every time you need to slightly reduce funding bias or slow decay by a small amount.

# 22. Suggested Initial Config Values

These are the recommended launch defaults.

```yaml
gravity: 1.4
age_buffer_hours: 3

category_multiplier:
  funding: 1.10
  launch: 1.10
  policy: 1.05
  engineering: 1.05
  ecosystem: 1.00
  opinion: 1.00
  ask: 1.00
  show: 1.00

comment_factor_cap: 0.25
comment_factor_scale: 0.05

domain_modifier_min: 0.85
domain_modifier_max: 1.05

comment_gravity: 1.2
comment_age_buffer_hours: 2
```

These values are intentionally conservative.

# 23. Worked Example

Assume a post has:

- weighted upvotes = `12`
- weighted downvotes = `0`
- comment count = `6`
- age = `8` hours
- category = `funding`
- domain modifier = `1.03`
- gravity = `1.4`

**Step 1: base vote score**

```text
base_vote_score = 12 - 0 + 1 = 13
```

**Step 2: comment factor**

```text
comment_factor = 1 + min(0.25, log2(6 + 1) * 0.05)
               = 1 + min(0.25, log2(7) * 0.05)
               ≈ 1 + min(0.25, 2.807 * 0.05)
               ≈ 1 + 0.14035
               ≈ 1.14035
```

**Step 3: hot score**

```text
hot_score = (13 * 1.14035) / ((8 + 3) ^ 1.4)
          ≈ 14.82455 / (11 ^ 1.4)
          ≈ 14.82455 / 28.67
          ≈ 0.517
```

**Step 4: category adjustment**

```text
category_adjusted_score = 0.517 * 1.10
                        ≈ 0.5687
```

**Step 5: domain adjustment**

```text
final_rank_score = 0.5687 * 1.03
                 ≈ 0.5858
```

This value is then stored as `posts.rank_score`.

# 24. What Not to Do in V1

Avoid these mistakes early.

## 24.1 Do not add ML ranking

There is not enough signal volume or stable training data yet.

## 24.2 Do not over-personalize

A common homepage is part of the product identity. Personalized feeds too early fragment the community signal layer.

## 24.3 Do not hide giant editorial biases inside math

If you need heavy intervention, use explicit moderation or curation.

## 24.4 Do not optimize for raw comment volume

That leads to outrage bait and noise.

## 24.5 Do not make rank behavior impossible to explain

Users should feel the system is broadly fair even if they do not know every coefficient.

# 25. Future Extensions

These are valid future additions, but not launch requirements.

## 25.1 Reputation-aware weighted voting

Introduce stronger trust weighting once the community is large enough and karma becomes meaningful.

## 25.2 Trend velocity metrics

Track acceleration of discussion, not just total score.

## 25.3 Country-aware ranking views

Example:

- Zimbabwe tech
- Kenya tech
- Nigeria fintech

This should be additive, not foundational in v1.

## 25.4 Personalized recommendation overlays

Keep the main feed intact, but later layer custom discovery surfaces.

## 25.5 Source- and topic-level trend dashboards

Useful for ecosystem intelligence products later.

# 26. Monitoring and Evaluation

The ranking system should be observed, not assumed to be correct.

## 26.1 Metrics to monitor

- average age of top feed posts
- duplicate submission rate
- comment-to-vote ratio
- number of posts with zero engagement
- moderation rate by domain and category
- concentration of top posts by domain
- concentration of top posts by small user groups
- feed refresh latency
- cache hit rate

## 26.2 Warning signals

You likely need tuning if:

- one domain dominates top feed too often
- new posts never surface
- old posts linger too long
- comment bait dominates
- ingested content suppresses native content
- job posts clutter main discovery surfaces
- low-quality self-promotion appears in top feed too easily

# 27. Recommended Launch Policy

The ranking system should launch with these defaults:

- `top` feed uses hot score with time decay
- `new` feed uses pure recency
- `ask` and `show` use category-filtered hot score
- `jobs` use separate recency-first logic
- public UI exposes upvotes only
- comments have thread-preserving score-aware ordering
- duplicate normalized URLs are rejected within the repost window
- blocked domains never rank
- domain trust applies only subtle influence
- category multipliers remain light
- rank scores are persisted and refreshed asynchronously

# 28. Summary

The ranking system is designed to fit a smaller, signal-sensitive ecosystem.

Its core properties are:

- slower decay than global high-volume communities
- simple enough to reason about
- resilient enough to resist obvious gaming
- flexible enough to evolve without rewriting the whole platform

The central logic is:

- start with vote signal
- add a small bounded discussion boost
- apply time decay
- lightly adjust for category and source trust
- persist `rank_score`
- serve hot feeds from cached snapshots

This produces a ranking model that is credible, tunable, and appropriate for an African tech discussion platform at MVP stage.
