# INGESTION_PIPELINE.md

## Project
**Working name:** RiftHub  
**System type:** Community-ranked discussion and discovery platform for African tech

---

# 1. Purpose

The ingestion pipeline is responsible for discovering, collecting, normalizing, and optionally publishing external tech ecosystem content into the platform.

This system exists to solve three major problems:

1. **Cold start problem**
2. **Discovery fragmentation**
3. **Signal aggregation**

Without ingestion, the platform depends entirely on manual user submissions. Early-stage communities rarely generate enough submissions to maintain a compelling feed.

The ingestion pipeline ensures the platform always has **fresh, relevant ecosystem content**, while still allowing the community to vote, comment, and rank that content organically.

---

# 2. Core Design Principles

The ingestion system must follow several strict principles.

## 2.1 Transparency

Ingested content must be clearly attributable to its source.

Users should be able to see:

- where the story came from
- whether it was auto-ingested
- the original publication

The platform should never pretend that externally sourced content is native.

---

## 2.2 Community-first ranking

Ingested stories should **not bypass the ranking system**.

Once published, they must:

- compete with user submissions
- rise or fall based on votes and discussion

The ingestion system only solves discovery. It should not control what becomes important.

---

## 2.3 Source quality control

Not all external sources are equal.

The ingestion pipeline must allow:

- trusted sources
- experimental sources
- paused sources
- disabled sources

This prevents low-quality feeds from polluting the ecosystem.

---

## 2.4 Deduplication

The same story should never appear multiple times.

Deduplication must occur at multiple layers:

- URL normalization
- ingestion item comparison
- existing post lookup

---

## 2.5 Moderation compatibility

The ingestion pipeline must integrate cleanly with moderation.

Moderators must be able to:

- review ingestion items
- approve or reject them
- pause sources
- disable sources
- downgrade trust levels
- reclassify categories

---

# 3. High-Level Architecture

The ingestion system consists of several stages.

```text
Sources
↓
Source Polling
↓
Raw Item Discovery
↓
Normalization
↓
Deduplication
↓
Ingestion Lifecycle
↓
Classification
↓
Moderation Gate
↓
Post Creation
↓
Ranking System
```



Each stage performs a narrow responsibility.

---

# 4. Source Types

The platform should support multiple source types.

## 4.1 RSS feeds

Primary ingestion mechanism.

Most tech blogs and publishers expose RSS.

Examples:

- TechCabal
- Techpoint Africa
- Benjamindada
- Disrupt Africa
- StartupList Africa
- VC newsletters with RSS feeds

RSS is reliable, structured, and easy to parse.

---

## 4.2 Structured APIs

Some platforms provide APIs for retrieving stories.

Examples:

- media outlets
- research platforms
- startup databases

These can be integrated as custom connectors.

---

## 4.3 Manual moderator sources

Moderators can manually submit content into ingestion staging.

Use cases:

- curated ecosystem events
- policy updates
- major funding announcements

---

## 4.4 Web scraping (limited use)

Scraping should be used carefully.

Problems:

- fragile parsing
- legal considerations
- changing HTML structures

Only use scraping when:

- no RSS exists
- the source is extremely valuable
- the extraction logic is stable

---

# 5. Source Registry

All ingestion sources are stored in the `sources` table.

Each source contains metadata controlling ingestion behavior.

Example fields:

| Field | Purpose |
| --- | --- |
| id | unique identifier |
| name | source name |
| source_type | rss / api / manual / scraper |
| status | active / paused / disabled |
| url | feed endpoint |
| site_url | base website |
| default_category | suggested category |
| trust_score | source quality and review policy input |
| auto_publish | skip manual review for trusted sources |
| poll_interval_minutes | ingestion frequency |
| last_checked_at | monitoring |
| last_success_at | monitoring |
| last_error_at | monitoring |

---

# 6. Polling System

The polling system is responsible for retrieving new items from sources.

## 6.1 Polling frequency

Each source defines its own polling interval.

Typical values:

| Source type | Interval |
| --- | --- |
| large publishers | 15–30 minutes |
| medium blogs | 60 minutes |
| niche blogs | 3–6 hours |
| slow sources | daily |

---

## 6.2 Polling workflow

```text
scheduler
↓
select active sources
↓
check poll interval
↓
fetch feed
↓
extract items
↓
store raw ingestion items
```


---

## 6.3 Failure handling

If polling fails:

- record `last_error_at`
- record error message
- do not crash the pipeline

Sources with repeated errors can be:

- paused automatically
- flagged for operator review

---

# 7. Raw Item Discovery

When polling retrieves a feed, each item becomes an **ingestion candidate**.

Typical RSS fields:

- title
- url
- publication date
- summary
- author
- tags

These items are **not posts yet**.

They are stored in `ingestion_items`.

---

# 8. Normalization

Normalization standardizes items before further processing.

Steps include:

## 8.1 URL normalization

Normalize URLs by removing noise.

Examples:

```text
https://example.com/story?utm_source=twitter
→
https://example.com/story
```



Remove:

- tracking parameters
- fragment identifiers
- duplicate query strings

---

## 8.2 Canonical host detection

Map URLs to their domain record.

Example:

```text
techcabal.com
→ domain entry
```


---

## 8.3 Title cleanup

Normalize titles by:

- trimming whitespace
- removing duplicated punctuation
- ensuring proper UTF encoding

---

## 8.4 Timestamp normalization

Convert publication timestamps to UTC.

---

# 9. Deduplication

Deduplication is essential.

Without it, multiple sources linking to the same story will create duplicates.

---

## 9.1 URL dedupe

First dedupe check:

```text
posts.url_normalized == ingestion_item.url_normalized
```


If a match exists:

- link ingestion item to existing post
- mark item as `duplicate`

---

## 9.2 Cross-source dedupe

Sometimes multiple sources link to the same article.

Example:

```text
TechCabal article
Disrupt Africa referencing same article
```

To prevent duplicates:

- compare normalized URLs
- optionally detect canonical URL from HTML

---

## 9.3 Repost window

If the same URL appears again within a defined window:

Example:

```text
repost_window_days = 30
```

Then reject duplicate submissions automatically.

---

# 10. Ingestion Lifecycle

After discovery, normalization, and dedupe checks, items move through the ingestion lifecycle.

Possible persisted statuses:

| Status | Meaning |
| --- | --- |
| discovered | raw item collected |
| normalized | cleaned and standardized |
| duplicate | matched existing post |
| classified | category assigned |
| awaiting_review | moderation needed before publication |
| published | post created |
| rejected | not suitable for publication |
| failed | processing error or unrecoverable pipeline failure |

---

# 11. Classification

The classification stage assigns a category.

Categories align with the platform taxonomy.

Example:

| Category | Meaning |
| --- | --- |
| `funding` | startup funding news |
| `launch` | new products |
| `engineering` | technical work |
| `ecosystem` | general ecosystem developments |
| `policy` | regulation and government |
| `opinion` | commentary |
| `jobs` | hiring |

---

## 11.1 Source-based classification

Many sources are consistent enough that their items can inherit a default category.

Example:

```text
source.default_category = funding
```

---

## 11.2 Title keyword classification

Basic heuristics can improve categorization.

Examples:

```text
"raises"   → funding
"launches" → launch
"hiring"   → jobs
"policy"   → policy
```

---

## 11.3 Manual correction

Moderators should be able to override classification easily.

---

# 12. Moderation Gate

Not all ingested items should publish automatically.

Sources are divided into trust tiers.

---

## 12.1 Auto-publish sources

High-trust publishers may bypass moderation.

Example:

- TechCabal
- Techpoint Africa
- Disrupt Africa

Pipeline:

```text
discover → normalize → classify → publish
```

---

## 12.2 Review-required sources

Lower-trust sources require moderation.

Pipeline:

```text
discover → normalize → classify → awaiting_review → publish or reject
```

Moderators can:

- approve
- reject
- change category
- edit title

---

# 13. Post Creation

Approved ingestion items become posts.

Fields populated:

| Field | Value |
| --- | --- |
| title | ingestion title |
| url | normalized URL |
| post_type | link |
| category | classified category |
| author_id | system user |
| domain_id | mapped domain |
| is_ingested | true |
| submitted_at | ingestion time |

---

## 13.1 System user

Ingested posts should be attributed to a system identity.

Example:

```text
@beacon-bot
```

or

```text
@source-techcabal
```


This preserves transparency.

---

# 14. Ranking Integration

Once published, ingested posts enter the same ranking system as user posts.

They receive:

- vote signals
- comment signals
- time decay

There should be **no hidden priority boost** for ingested content.

---

# 15. Cold Start Strategy

In the early months, ingestion will carry most of the feed.

Recommended approach:

1. seed 15–30 trusted sources
2. enable auto-publish for high-trust sources
3. allow community ranking to surface signal

Over time, organic submissions should grow.

---

# 16. Operational Monitoring

Operators should track ingestion health.

Key metrics:

| Metric | Meaning |
| --- | --- |
| items discovered per day | ingestion volume |
| publish rate | moderation acceptance |
| duplicate rate | dedupe efficiency |
| error rate | source stability |
| ingestion latency | freshness |

---

# 17. Failure Recovery

The ingestion system must tolerate failure.

Possible failures:

- source unavailable
- malformed RSS
- parsing errors
- network timeouts

Recovery steps:

- retry later
- log error
- avoid crashing workers

---

# 18. Ingestion Worker Model

Recommended architecture:

```text
scheduler
↓
polling workers
↓
normalization workers
↓
classification workers
↓
moderation queue
↓
post creation workers
```

Workers should be stateless and horizontally scalable.

---

# 19. Cache Interaction

Ingestion events may invalidate feed caches.

When a new post is published:

- invalidate top feed cache
- invalidate category feeds

This ensures fresh stories appear quickly.

---

# 20. Security Considerations

External ingestion introduces risk.

Possible issues:

- malicious RSS payloads
- malformed HTML
- spam sources
- injection attempts

Mitigations:

- sanitize titles
- sanitize extracted text
- limit field lengths
- never trust external HTML blindly

---

# 21. Future Improvements

The ingestion system can evolve.

Potential improvements:

### Source reputation scoring

Automatically adjust trust levels based on moderation outcomes.

### ML-based classification

Improve category detection.

### Trending detection

Highlight ecosystem events across multiple sources.

### Startup database integration

Automatically surface funding announcements.

### Event detection

Detect conferences, hackathons, accelerator cohorts.

---

# 22. Launch Recommendations

For MVP launch:

- start with **20–30 trusted RSS sources**
- enable auto-publish for high-quality publishers
- require review for experimental sources
- enforce strict URL dedupe
- integrate ingestion directly with ranking system

This provides:

- continuous ecosystem coverage
- early feed quality
- community discussion opportunities

---

# 23. Summary

The ingestion pipeline acts as the **ecosystem radar** for the platform.

It:

- discovers relevant tech stories
- normalizes and deduplicates them
- classifies them
- passes review-required items through moderation
- publishes them into the ranking system

If implemented correctly, the pipeline ensures the platform always reflects the **current state of the African tech ecosystem** while still letting the community decide what matters most.
