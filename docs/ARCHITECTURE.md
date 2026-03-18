# Project's Architecture
**Working name:** RiftHub  
**Product type:** Community-ranked discussion and discovery platform for African tech

> The pulse of African tech — curated by the community



# 1. Purpose

This document defines the architecture of the platform: product scope, system boundaries, domain model, backend services, ranking logic, moderation rules, infrastructure, and deployment topology.

The goal is to build a feed-first platform where the homepage acts as the primary product surface. Users submit links or native posts, the community votes and comments, and the system ranks stories into multiple feeds such as `top`, `new`, `ask`, `show`, and `jobs`.

This is **not** a generic forum. It is a **signal aggregation and discussion layer** for the African tech ecosystem.


# 2. Product Goals

## 2.1 Primary goals

- Create a single destination for discovering important African tech stories and discussions
- Rank content through a mix of community votes, time decay, and moderation controls
- Support both external link submissions and native text discussions
- Make the homepage useful even before the community fully matures
- Build a system that can later expand into ecosystem intelligence, startup discovery, and trend analysis

## 2.2 Non-goals for v1

The following are explicitly out of scope for the first version:

- Personalized recommendation feeds
- Machine-learning ranking
- Private messaging
- Team workspaces
- Rich media posting
- Country-level subcommunities
- Advanced notifications system
- Full-text semantic search
- Mobile apps
- Complex reputation economies
- Real-time chat

[Note: these will be recommended when building v2]

# 3. High-Level Product Model

At a high level, the platform consists of:

- **Users** who browse, submit, vote, and comment
- **Posts** which may be links, text posts, or jobs
- **Comments** which form threaded discussions
- **Votes** that influence ranking
- **Categories** that label the nature of a post
- **Feeds** that expose ranked or filtered views of content
- **Moderation tools** that preserve quality
- **Ingestion pipelines** that solve the cold-start problem


# 4. Core User Experience

## 4.1 Homepage

The homepage is a dense ranked feed of stories. Each item typically displays:

- rank
- vote count
- category badge
- title
- source domain
- author
- age
- comment count

## 4.2 Post detail page

A post detail page displays:

- title
- source URL or text content
- metadata
- threaded comments
- voting controls
- moderation status if applicable

## 4.3 Submission flows

Users can submit:

- external links
- text posts
- jobs

## 4.4 Feed tabs

Initial feed tabs:

- `top`
- `new`
- `ask`
- `show`
- `jobs`

Optional later additions:

- `funding`
- `policy`
- `launches`
- `dev`

---

# 5. Content Model

## 5.1 Post types

A **post type** controls how the object behaves technically.

Initial supported post types:

- `link` — an external URL submission
- `text` — a native post hosted on-platform
- `job` — a job listing

## 5.2 Categories

A **category** describes editorial or thematic classification.

Initial categories:

- `funding`
- `launch`
- `policy`
- `opinion`
- `ask`
- `show`
- `jobs`
- `engineering`
- `ecosystem`

A post has one primary category in v1. Multi-category support can be added later if necessary.

## 5.3 Why type and category are separate

A post type affects storage and rendering. A category affects classification and feed behavior.

Examples:

- `Ask RiftHub: Best local cloud hosting options?`  
  `post_type = text`, `category = ask`

- `Flutterwave raises $17M...`  
  `post_type = link`, `category = funding`

- `Senior Backend Engineer at Chipper Cash`  
  `post_type = job`, `category = jobs`


# 6. Feed Definitions

Each feed must have a strict technical definition.

## 6.1 `top`
Posts ranked by a hot-score formula using votes and time decay.

## 6.2 `new`
Posts ordered by creation time descending.

## 6.3 `ask`
Text posts where `category = ask`.

## 6.4 `show`
Posts where `category = show`.

## 6.5 `jobs`
Job posts ordered primarily by recency, with optional light ranking.

## 6.6 Future feeds
Potential later feeds include:

- `funding`
- `policy`
- `launches`
- `companies`
- `country/<country_code>`

These are not required for v1.


# 7. System Architecture Overview

## 7.1 Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, Tailwind CSS, TypeScript |
| Backend API | FastAPI |
| ORM | SQLAlchemy (async) |
| Migrations | Alembic |
| Database | PostgreSQL via Supabase |
| Cache / Rate Limiting | Redis via Upstash |
| Frontend Hosting | Vercel |
| Backend Hosting | Railway |
| Object Storage | optional later |
| Background Jobs | lightweight async worker / Railway worker process |

## 7.2 Architectural style

The system will use a **modular monolith** at first, not microservices.

Reasoning:

- lower operational complexity
- easier iteration
- better fit for early-stage product development
- ranking, moderation, and content logic are tightly coupled early on

The backend should be structured into internal modules, but deployed as one primary API service.


# 8. Top-Level Components

## 8.1 Frontend application

Responsibilities:

- render feeds
- render post detail pages
- render submission forms
- handle auth session state
- call backend APIs
- support optimistic UI for voting where safe

## 8.2 Backend API service

Responsibilities:

- authentication and authorization
- post CRUD
- comment CRUD
- vote handling
- feed query generation
- moderation actions
- ingestion endpoints and admin operations
- score computation orchestration

## 8.3 Database

Responsibilities:

- durable source of truth for users, posts, comments, votes, moderation, and ingestion metadata

## 8.4 Redis

Responsibilities:

- hot feed cache
- rate limiting
- short-lived counters
- duplicate detection support
- worker coordination locks
- temporary ranking snapshots

## 8.5 Background worker

Responsibilities:

- recompute scores
- process ingestion feeds
- normalize URLs
- deduplicate inbound submissions
- refresh cached feed snapshots
- run housekeeping tasks


# 9. Request / Data Flow

## 9.1 Reading the home feed

1. User requests `/top`
2. Frontend calls backend feed endpoint
3. Backend checks Redis cached feed snapshot
4. If cache exists and is fresh, return ranked post IDs + metadata
5. If cache miss or stale:
   - query Postgres
   - compute or fetch latest score ordering
   - store snapshot in Redis
   - return response

## 9.2 Submitting a link

1. User submits title + URL + category
2. Backend normalizes URL
3. Backend extracts canonical domain
4. Backend checks duplicate fingerprints
5. If duplicate exists:
   - redirect user to existing post, or
   - allow moderated merge behavior later
6. If new:
   - create post row
   - seed initial score
   - enqueue score refresh
   - invalidate relevant feed caches

## 9.3 Voting on a post

1. User sends vote action
2. Backend validates auth and rate limits
3. Backend upserts vote row
4. Backend updates aggregate counters
5. Backend recalculates score or queues recalculation
6. Relevant cache keys are invalidated or lazily refreshed

## 9.4 Posting a comment

1. User submits comment body and optional parent ID
2. Backend validates nesting rules
3. Comment is stored
4. Comment counts and post activity timestamps are updated
5. Comment tree cache is invalidated


# 10. Backend Module Design

The backend should be organized by domain modules.

## 10.1 Auth module

Responsibilities:

- user registration
- login
- session/JWT issuance
- password hashing
- role checks

## 10.2 Users module

Responsibilities:

- profiles
- karma totals
- activity summaries
- account status

## 10.3 Posts module

Responsibilities:

- submission validation
- post creation
- post retrieval
- post editing constraints
- hide/delete state transitions

## 10.4 Comments module

Responsibilities:

- threaded comments
- comment editing rules
- nesting depth rules
- comment tree retrieval

## 10.5 Votes module

Responsibilities:

- post votes
- comment votes
- vote reversal handling
- anti-abuse constraints

## 10.6 Feeds module

Responsibilities:

- top feed
- new feed
- category feeds
- jobs feed
- pagination

## 10.7 Ranking module

Responsibilities:

- score calculation
- decay logic
- category weighting
- domain trust penalties or boosts
- cache snapshot generation

## 10.8 Moderation module

Responsibilities:

- flags
- hide/remove/lock actions
- domain trust rules
- moderator audit logs

## 10.9 Ingestion module

Responsibilities:

- RSS source management
- source polling
- parsed candidate posts
- deduplication
- approval queue or auto-publish logic


# 11. Database Design

## 11.1 Core principles

- Keep one `posts` table for all top-level submissions
- Use enums where stable, lookup tables where future expansion is likely
- Denormalize counts only where read performance benefits materially
- Record moderation actions in an immutable audit table
- Avoid premature table explosion

## 11.2 Core tables

### `users`
Stores user accounts.

Suggested columns:

- `id`
- `username`
- `email`
- `password_hash`
- `bio`
- `role`
- `status`
- `karma`
- `created_at`
- `updated_at`
- `last_active_at`

### `posts`
Stores all top-level content.

Suggested columns:

- `id`
- `author_id`
- `post_type` (`link`, `text`, `job`)
- `category`
- `title`
- `slug`
- `url`
- `url_normalized`
- `domain_id`
- `body_markdown`
- `status` (`active`, `hidden`, `removed`, `locked`)
- `score`
- `upvote_count`
- `downvote_count`
- `comment_count`
- `rank_score`
- `submitted_at`
- `updated_at`

### `comments`
Stores threaded comments.

Suggested columns:

- `id`
- `post_id`
- `author_id`
- `parent_comment_id` nullable
- `body_markdown`
- `status`
- `score`
- `upvote_count`
- `downvote_count`
- `depth`
- `created_at`
- `updated_at`

### `post_votes`
Stores one vote per user per post.

Suggested columns:

- `id`
- `post_id`
- `user_id`
- `vote_value` (`1` or `-1`, or only `1` if downvotes are disabled)
- `created_at`
- `updated_at`

Unique constraint:

- `(post_id, user_id)`

### `comment_votes`
Stores one vote per user per comment.

Suggested columns:

- `id`
- `comment_id`
- `user_id`
- `vote_value`
- `created_at`
- `updated_at`

Unique constraint:

- `(comment_id, user_id)`

### `domains`
Tracks source domains.

Suggested columns:

- `id`
- `hostname`
- `display_name`
- `trust_score`
- `is_blocked`
- `submission_count`
- `created_at`
- `updated_at`

### `flags`
Tracks user reports.

Suggested columns:

- `id`
- `target_type` (`post`, `comment`, `user`)
- `target_id`
- `reporter_id`
- `reason_code`
- `notes`
- `status`
- `created_at`
- `resolved_at`

### `moderation_actions`
Immutable moderation audit log.

Suggested columns:

- `id`
- `moderator_id`
- `target_type`
- `target_id`
- `action_type`
- `reason`
- `metadata_json`
- `created_at`

### `sources`
Tracks ingestion sources such as RSS feeds.

Suggested columns:

- `id`
- `name`
- `source_type` (`rss`, `manual`, `scraper`)
- `url`
- `is_active`
- `default_category`
- `trust_level`
- `last_checked_at`
- `last_success_at`
- `created_at`

### `ingestion_items`
Tracks fetched candidates before or after publication.

Suggested columns:

- `id`
- `source_id`
- `external_id`
- `title`
- `url`
- `url_normalized`
- `published_at_external`
- `raw_payload_json`
- `ingestion_status` (`new`, `deduped`, `queued`, `published`, `rejected`)
- `linked_post_id` nullable
- `created_at`

## 11.3 Optional later tables

- `bookmarks`
- `notifications`
- `user_settings`
- `followed_topics`
- `daily_stats`
- `post_score_history`


# 12. Enum Definitions

## 12.1 User role enum

- `user`
- `moderator`
- `admin`

## 12.2 User status enum

- `active`
- `suspended`
- `banned`

## 12.3 Post type enum

- `link`
- `text`
- `job`

## 12.4 Post status enum

- `active`
- `hidden`
- `removed`
- `locked`

## 12.5 Comment status enum

- `active`
- `hidden`
- `removed`
- `locked`

## 12.6 Category enum

- `funding`
- `launch`
- `policy`
- `opinion`
- `ask`
- `show`
- `jobs`
- `engineering`
- `ecosystem`


# 13. Ranking System

## 13.1 Design goals

The ranking algorithm should:

- reward posts receiving genuine engagement
- allow fresh stories to surface quickly
- decay older stories over time
- resist spam and low-trust domains
- remain understandable and tunable

## 13.2 Initial score model

Recommended initial hot-ranking model:

```text
base_score = (weighted_upvotes - weighted_downvotes + 1)
rank_score = base_score / ((age_hours + 3) ^ gravity)
```

Where:
-  `gravity` initially starts around `1.4`
- `age_hours` is time since submission
- `weighted_upvotes` and `weighted_downvotes` may later use user karma weighting

## 13.3 Why RiftHub should have lower gravity

The ecosystem will definitely start smaller and produce less volume. A lower gravity will help keep good stories visible longer and prevent the homepage from turning over too aggressively.

## 13.4 Category multipliers

A light category multiplier may be applied after the base rank if needed.

Example:

- `funding: 1.10`
- `launch: 1.10`
- `policy: 1.05`
- `opinion: 1.00`
- `jobs: separated feed, so usually no multiplier in top`

This must be used sparingly. Heavy editorial weighting will undermine trust.


## 13.5 Domain trust modifier

Low-trust domains may receive a penalty or require stronger engagement before ranking highly.

Example conceptual modifier:

```text
adjusted_score = rank_score * domain_modifier
```

Where `domain_modifier` may range from `0.85 to 1.05`.

## 13.6 Commenting ranking

Initial comment score can be simpler:

```text
comment_rank = (upvotes - downvotes + 1) / ((age_hours + 2) ^ 1.2)
```

Comments should be ordered primarily by thread structure plus score.


## 13.7 Score recomputation strategy

Use a hybrid approach:

- recompute on write for local object updates
- run periodic background refresh jobs for feed snapshots
- cache final feed order in Redis


# Voting Rules

## 14.1 Initial recommendation

Start with:

- post upvotes only
- comment upvotes only

Avoid public downvotes in v1 unless there is a strong moderation need.

Reason:

- simpler mental model
- lower toxicity risk
- reduced brigading surface
- more consistent early community tone

Internally, moderator can still have stronger controls


## 14.2 Vote constraints

- one vote per user per entity
- users cannot vote on their own content
- anonymous voting is not allowed
- voting requires verified/authenticated user status


## 14.3 Vote write behavior

Use an upsert pattern:

- insert new vote if none exists
- remove if user toggles same vote again
- update aggregates transactionally
- recalculate object score


# Comment Tree Strategy

## 15.1 Threading model

Use adjacency list storage:

- each comment stores `parent_comment_id`
- top-level comments have null parent
- `depth` is stored for convenience and validation


## 15.2 Nesting limits

Set a maximum nesting depth in v1 to preserve readability. Recommended:

- max depth = 6


## 15.3 Rendering strategy

Frontend should render recursively but collapse deep or low-score branches where needed.

## 15.4 Editing and deletion

Users may edit comments within a limited time window. Deletions should generally be soft deletes preserving thread structure.

# 16. Duplicate Detection

Duplicate link handling is essential.

## 16.1 URL normalization

Normalize URLs before checking uniqueness:
- lowercase hostname
- strip tracking parameters (utm_*, etc.)
- normalize scheme where appropriate
- resolve trailing slashes
- canonicalize known domains if possible

## 16.2 Duplicate policy

If the same normalized URL already exists:
- reject the new submission and redirect to existing post, or
- allow submission only if prior post is very old and policy permits reposts

## 16.3 Similar-content detection

Later, semantic similarity can be added for near-duplicate headlines. Not required for v1.


# 17. Moderation Model

## 17.1 Moderation goals

- prevent spam
- preserve discussion quality
- keep feeds useful
- prevent manipulation

## 17.2 Initial moderation actions

Moderators can:
- hide post
- remove post
- lock post
- hide comment
- remove comment
- suspend user
- ban user
- adjust domain trust
- reclassify category

## 17.3 Flagging flow

Users can report posts/comments. Flags go into a queue visible to moderators.

## 17.4 Auditability

Every moderator action must be written to moderation_actions.

## 17.5 Soft deletion

Prefer soft deletion for auditability and thread stability.


# 18. Ingestion and Cold-Start Strategy

## 18.1 Why ingestion exists

A community platform without content dies early. The platform needs a mechanism to import relevant external stories so the homepage remains populated.

## 18.2 Initial ingestion method

Use RSS where available. This is the simplest and most reliable starting point.

Flow:
1.	poll source feeds
2.	parse entries
3.	normalize URLs
4.	dedupe against existing posts
5.	classify into candidate category
6.	auto-publish or queue for moderator review

## 18.3 Auto-publish vs review

Recommended v1 approach:
- trusted sources may auto-publish
- lower-trust sources go to review queue

## 18.4 Source trust model

Each source gets a trust level used for:
- auto-publish permissions
- domain weighting
- ingestion priority


# 19. API Design

## 19.1 API style

Use REST for v1. It is sufficient, easy to debug, and fits the current scope.

GraphQL will be introduced in v2.

## 19.2 Endpoint groups

Auth
- `POST /auth/register`
- `POST /auth/verify`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`

Users
- `GET /users/{username}`
- `GET /users/{username}/posts`
- `GET /users/{username}/comments`

Posts
- `GET /posts`
- `POST /posts`
- `GET /posts/{post_id}`
- `PATCH /posts/{post_id}`
- `DELETE /posts/{post_id}`

Comments
- `POST /posts/{post_id}/comments`
- `GET /posts/{post_id}/comments`
- `PATCH /comments/{comment_id}`
- `DELETE /comments/{comment_id}`

Votes
- `POST /posts/{post_id}/vote`
- `DELETE /posts/{post_id}/vote`
- `POST /comments/{comment_id}/vote`
- `DELETE /comments/{comment_id}/vote`

Feeds
- `GET /feeds/top`
- `GET /feeds/new`
- `GET /feeds/ask`
- `GET /feeds/show`
- `GET /feeds/jobs`

Moderation
- `POST /moderation/posts/{post_id}/hide`
- `POST /moderation/posts/{post_id}/lock`
- `POST /moderation/comments/{comment_id}/hide`
- `POST /moderation/users/{user_id}/suspend`

Ingestion / Admin
- `GET /admin/sources`
- `POST /admin/sources`
- `POST /admin/ingestion/run`
- `GET /moderation/flags`

## 19.3 Pagination

Use cursor-based pagination for feeds and comments where possible. Offset pagination may be acceptable initially for admin tooling.


# 20. Authentication and Authorization

## 20.1 Auth model

Use secure session or JWT-based auth. If frontend and backend are split across domains, carefully handle cookies, CSRF, and CORS.

## 20.2 Password storage

Store only strong password hashes using a modern password hashing algorithm.

## 20.3 Authorization

Role-based checks are sufficient in v1:
- guest
- authenticated user
- moderator
- admin

## 20.4 Trust gating

Later, feature gates may depend on account age, karma, or verification state.


# 21. Caching Strategy

## 21.1 What should be cached

Redis should cache:
- hot feed snapshots
- individual post metadata hot paths
- comment tree snapshots for active threads
- rate-limit counters
- duplicate URL lookup helpers

## 21.2 Cache invalidation events

Invalidate relevant cache keys when:
- a post is created
- a vote changes
- a comment is added
- a moderation action changes visibility
- ingestion publishes new content

## 21.3 Cache TTLs

Recommended initial TTLs:
- top feed snapshot: 30 to 120 seconds
- new feed snapshot: 30 seconds
- post detail metadata: 60 seconds
- comment tree snapshot: 30 to 60 seconds

These values should be tuned after observing load and update frequency.


# 22. Background Jobs

## 22.1 Initial job types
- feed snapshot recomputation
- score refresh
- ingestion polling
- stale cache warming
- housekeeping / cleanup
- spam heuristics batch scans

## 22.2 Execution model

A simple worker process is enough initially. Do not introduce a heavy distributed orchestration system unless the workload requires it.


# 23. Search

Search is not a v1 core dependency. If implemented early, keep it simple:
- title search
- domain filter
- category filter
- author filter

Full semantic search can wait. To be implemented in v2.


# 24. Frontend Architecture

## 24.1 Frontend principles
- render real backend data early
- prefer server rendering for feed pages
- keep client state minimal
- isolate API layer cleanly
- optimize for information density, not animation

## 24.2 Initial routes
- `/`
- `/new`
- `/ask`
- `/show`
- `/jobs`
- `/submit`
- `/post/[id]`
- `/user/[username]`
- `/login`
- `/register`

## 24.3 Component groups
- layout shell
- nav/header
- stats strip
- feed list
- feed row
- vote control
- category badge
- comment tree
- submit form
- moderator controls


# 25. Observability

## 25.1 Logging

Use structured application logs in backend services.

## 25.2 Metrics to track
- daily active users
- posts per day
- comments per day
- votes per day
- feed request latency
- cache hit rate
- duplicate rejection rate
- moderation action count
- ingestion success/failure rate

# 25.3 Error tracking

Capture backend and frontend exceptions with a proper error monitoring tool.


# 26. Security Considerations

## 26.1 Core application security
- rate limit auth and submission endpoints
- sanitize user content
- validate and normalize all URLs
- protect against XSS in rendered markdown
- use CSRF protection where relevant
- lock down moderator/admin routes
- audit sensitive actions

## 26.2 Abuse prevention
- account creation throttles
- vote throttling heuristics
- submission quotas
- spam domain blocklists
- moderation queue for suspicious posts


# 27. Performance Considerations

## 27.1 Feed performance

The feed is the primary read path. Optimize for:
- indexed post retrieval
- cached rank snapshots
- minimal over-fetching
- precomputed counts where justified

## 27.2 Suggested indexes

**posts**
- index on `submitted_at` `DESC`
- index on `rank_score` `DESC`
- index on (`category`, `submitted_at` `DESC`)
- index on (`status`, `rank_score` `DESC`)

**comments**
- index on `post_id`
- index on `parent_comment_id`
- index on (`post_id`, `created_at` `ASC`)

**post_votes**
- unique index on (`post_id`, `user_id`)

**comment_votes**
- unique index on (`comment_id`, `user_id`)

**domains**
- unique index on `hostname`

# 28. Deployment Topology

## 28.1 Frontend

Deploy Next.js frontend on Vercel.

## 28.2 Backend

Deploy FastAPI app on Railway.

## 28.3 Database

Use Supabase Postgres as primary database.

## 28.4 Cache

Use Upstash Redis.

## 28.5 Worker

Run background worker on Railway as a separate service.

## 28.6 Environment boundaries

Use separate environments:
- development
- staging
- production

Never share production data or credentials with development.


# 29. Local Development Model

## 29.1 Recommended local stack
- frontend running locally with Next.js
- backend running locally with FastAPI
- local Postgres via Docker or managed dev DB
- local Redis via Docker if possible

## 29.2 Development principles
- run migrations locally
- use seed scripts for realistic feed data
- keep a fixture set of posts/comments/votes for UI testing


# 30 Summary

The system should be built as a modular monolith centered on one primary concept: a ranked, community-driven feed of African tech stories and discussions.

The architecture prioritizes:
- strong content primitives
- clear feed definitions
- durable moderation controls
- manageable operational complexity
- a cold-start strategy through ingestion
- room to evolve into a broader ecosystem intelligence product

The most important engineering truth is that the product is not the UI shell. The product is the interaction between submission, voting, ranking, discussion, and moderation. Every architectural decision should preserve the quality and credibility of that loop.
