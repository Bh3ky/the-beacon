# DATABASE_SCHEMA.md

## Project
**Working name:** RiftHub

**System type:** Community-ranked discussion and discovery platform for African tech



# 1. Purpose

This document defines the relational database schema for the platform.

The schema is designed to support:

- user accounts and roles
- top-level submissions (`link`, `text`, `job`)
- threaded comments
- voting
- feed ranking
- moderation actions
- source/domain trust
- ingestion from external publishers

This schema is intended for **PostgreSQL** and will be implemented via **SQLAlchemy (async)** with **Alembic** migrations.



# 2. Design Principles

## 2.1 Core principles

The schema follows these principles:

1. **One table for all top-level posts**
   - A single `posts` table is easier to reason about than separate link/text/job tables.
   - Differences between post kinds are handled through `post_type`.

2. **Soft deletion over hard deletion**
   - Content and moderation history should remain auditable.
   - Visibility is controlled through status fields.

3. **Strict uniqueness where interaction semantics require it**
   - One user can only cast one vote per entity.
   - Domains are unique by canonical hostname.
   - URL normalization is used to reduce duplicate submissions.

4. **Counts may be denormalized for performance**
   - `upvote_count`, `comment_count`, and `rank_score` are stored on hot entities.
   - They remain derivable from source tables if needed.

5. **Moderation is first-class**
   - Audit history is never implicit.
   - Moderator actions are written to dedicated tables.

6. **Ingestion is a first-class subsystem**
   - The cold-start problem is a product concern, so source and ingestion tables belong in core schema.



# 3. PostgreSQL Extensions and Conventions

## 3.1 Recommended extensions

Recommended PostgreSQL extensions:

- `pgcrypto` for UUID generation if using DB-generated UUIDs
- `citext` for case-insensitive username/email handling if desired

## 3.2 Naming conventions

- table names: plural snake_case
- column names: snake_case
- primary keys: `id`
- foreign keys: `<referenced_entity>_id`
- timestamp columns:
  - `created_at`
  - `updated_at`
- status/type columns use enums or constrained text

## 3.3 Primary key strategy

Recommended default:

- `UUID` primary keys for public-facing entities

This is preferred over sequential integers because:

- safer for public APIs
- harder to enumerate
- cleaner separation between internal storage and external exposure



# 4. Entity Relationship Overview

Core relationships:

- a `user` creates many `posts`
- a `user` creates many `comments`
- a `post` has many `comments`
- a `post` belongs to one `domain` when it is a link post
- a `user` can vote once per `post`
- a `user` can vote once per `comment`
- a `post` can receive many `flags`
- a `comment` can receive many `flags`
- a `moderator` creates many `moderation_actions`
- a `source` creates many `ingestion_items`
- an `ingestion_item` may map to one published `post`


# 5. Enum Definitions

These enums should be created at the database level for integrity and clarity.

## 5.1 `user_role_enum`

```text
user
moderator
admin
```

## 5.2 `user_status_enum`

```text
active
suspended
banned
```

## 5.3 `post_type_enum`

```text
link
text
job
```

## 5.4 `post_status_enum`

```text
active
hidden
removed
locked
```

## 5.5 `comment_status_enum`

```text
active
hidden
removed
locked
```


## 5.6 `category_enum`

```text
funding
launch
policy
opinion
ask
show
jobs
engineering
ecosystem
```


## 5.7 `flag_target_type_enum`

```text
post
comment
user
```


## 5.8 `flag_status_enum`

```text
open
reviewing
resolved
dismissed
```


## 5.9 `flag_reason_enum`

```text
spam
abuse
misinformation
off_topic
other
```


## 5.10 `moderation_target_type_enum`

```text
post
comment
user
domain
source
```

## 5.11 `moderation_action_type_enum`

```text
hide
remove
lock
unlock
restore
reclassify
suspend_user
ban_user
unsuspend_user
set_domain_trust
block_domain
unblock_domain
approve_ingestion
reject_ingestion
```

## 5.12 `source_type_enum`

```text
rss
manual
scraper
api
```


## 5.13 `source_status_enum`

```text
active
paused
disabled
```

Operational meaning:

- `active` = source is eligible for polling
- `paused` = source is temporarily disabled without being considered blocked
- `disabled` = source is hard-disabled or operationally blocked

## 5.14 `ingestion_status_enum`

```text
discovered
normalized
duplicate
classified
awaiting_review
published
rejected
failed
```

# 6. Core Tables

## 6.1 `users`

Stores registered user accounts.

**Columns**

| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | UUID | no | primary key |
| `username` | VARCHAR(32) | no | unique; canonical public handle |
| `email` | VARCHAR(255) | no | unique |
| `password_hash` | TEXT | no | hashed password only |
| `bio` | TEXT | yes | optional profile bio |
| `role` | `user_role_enum` | no | default `user` |
| `status` | `user_status_enum` | no | default `active` |
| `karma` | INTEGER | no | default `0` |
| `post_count` | INTEGER | no | default `0` |
| `comment_count` | INTEGER | no | default `0` |
| `avatar_url` | TEXT | yes | optional; can be external or storage-backed |
| `last_active_at` | TIMESTAMPTZ | yes | updated on relevant activity |
| `created_at` | TIMESTAMPTZ | no | default now() |
| `updated_at` | TIMESTAMPTZ | no | default now() |


**Constraints**

- `username` unique
- `email` unique
- `karma >= 0` is not required; karma may go negative later if downvotes or moderation penalties exist
- recommended username check:
  - length 3–32
  - lowercase canonical storage
  - allowed chars: `[a-z0-9_]+`

**Indexes**

- unique index on `username`
- unique index on `email`
- index on `role`
- index on `status`
- index on `created_at desc`


## 6.2 `domains`

Stores canonical source domains for link posts.

**Purpose**

This table allows:

- deduplicated domain tracking
- trust scoring
- domain-level moderation
- future domain pages and analytics

**Columns**

| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | UUID | no | primary key |
| `hostname` | VARCHAR(255) | no | unique; canonical hostname |
| `display_name` | VARCHAR(255) | yes | human-friendly label |
| `trust_score` | NUMERIC(5,2) | no | default `1.00` |
| `is_blocked` | BOOLEAN | no | default `false` |
| `submission_count` | INTEGER | no | default `0` |
| `published_post_count` | INTEGER | no | default `0` |
| `last_seen_at` | TIMESTAMPTZ | yes | most recent submission or ingestion |
| `created_at` | TIMESTAMPTZ | no | default now() |
| `updated_at` | TIMESTAMPTZ | no | default now() |


**Constraints**

- unique on `hostname`
- `trust_score > 0`

**Indexes**

- unique index on `hostname`
- index on `is_blocked`
- index on `trust_score desc`


## 6.3 `posts`

Stores all top-level content objects.

This is the most important table in the system.

| Column                    | Type               | Null | Notes                                                        |
| ------------------------- | ------------------ | ---: | ------------------------------------------------------------ |
| `id`                      | UUID               |   no | primary key                                                  |
| `author_id`               | UUID               |   no | FK to `users.id`                                             |
| `post_type`               | `post_type_enum`   |   no | `link`, `text`, `job`                                        |
| `category`                | `category_enum`    |   no | primary classification                                       |
| `title`                   | VARCHAR(300)       |   no | post headline                                                |
| `slug`                    | VARCHAR(350)       |   no | URL-safe slug, not globally unique by itself unless chosen   |
| `url`                     | TEXT               |  yes | required for `link`/typically `job` if external              |
| `url_normalized`          | TEXT               |  yes | normalized URL for dedupe                                    |
| `domain_id`               | UUID               |  yes | FK to `domains.id`; null for pure text posts                 |
| `body_markdown`           | TEXT               |  yes | required for `text`; optional for `job`; null for many links |
| `status`                  | `post_status_enum` |   no | default `active`                                             |
| `is_ingested`             | BOOLEAN            |   no | default `false`                                              |
| `ingested_from_source_id` | UUID               |  yes | FK to `sources.id`                                           |
| `upvote_count`            | INTEGER            |   no | default `0`                                                  |
| `downvote_count`          | INTEGER            |   no | default `0`                                                  |
| `comment_count`           | INTEGER            |   no | default `0`                                                  |
| `score`                   | INTEGER            |   no | raw vote score or net score                                  |
| `rank_score`              | DOUBLE PRECISION   |   no | computed hot ranking score                                   |
| `bookmark_count`          | INTEGER            |   no | default `0`; optional future use                             |
| `view_count`              | INTEGER            |   no | default `0`; optional and eventually sampled                 |
| `submitted_at`            | TIMESTAMPTZ        |   no | semantic creation time for ranking                           |
| `created_at`              | TIMESTAMPTZ        |   no | default now()                                                |
| `updated_at`              | TIMESTAMPTZ        |   no | default now()                                                |
| `last_commented_at`       | TIMESTAMPTZ        |  yes | useful for active threads                                    |
| `job_expires_at`          | TIMESTAMPTZ        |  yes | only relevant for `job` posts                                |


**Required-field semantics by `post_type`**


`link`

- `url` required
- `url_normalized` required
- `domain_id` required
- `body_markdown` optional

`text`

- `body_markdown` required
- `url` null
- `url_normalized` null
- `domain_id` null

`job`

- `title` required
- may use external `url`, internal `body_markdown`, or both
- `job_expires_at` recommended

**Constraints**

Recommended check constraints:

1. **post type validity**

- if `post_type = 'text'`, then `body_markdown is not null`
- if `post_type = 'text'`, then `url is null`
- if `post_type = 'text'`, then `domain_id is null`


2. **link validity**

- if `post_type = 'link'`, then `url is not null`
- if `post_type = 'link'`, then `url_normalized is not null`
- if `post_type = 'link'`, then `domain_id is not null`

3. **job validity**

- more permissive; either `url` or `body_markdown` should exist

4. **counts**

- `upvote_count >= 0`
- `downvote_count >= 0`
- `comment_count >= 0`

**Uniqueness**

Recommended:

- unique partial index on `url_normalized` where `url_normalized is not null` and post is active or within repost window policy

Do not make `slug` globally unique by itself unless you want rigid slug collision handling. Safer options:

- `slug` non-unique, route by `id`
or unique on (`id, slug`) externally
or store a resolved unique slug per post

Recommended route design remains `/post/{id}/{slug}`.

**Indexes**

- index on `author_id`
- index on `category`
- index on `post_type`
- index on `status`
- index on `submitted_at desc`
- index on `rank_score desc`
- composite index on (`status, rank_score desc`)
- composite index on (`category, status, submitted_at desc`)
- composite index on (`post_type, status, submitted_at desc`)
- index on `domain_id`
- unique or partial unique index on `url_normalized`


## 6.4 `comments`

Store threaded comments on posts.

| Column              | Type                  | Null | Notes               |
| ------------------- | --------------------- | ---: | ------------------- |
| `id`                | UUID                  |   no | primary key         |
| `post_id`           | UUID                  |   no | FK to `posts.id`    |
| `author_id`         | UUID                  |   no | FK to `users.id`    |
| `parent_comment_id` | UUID                  |  yes | self-referencing FK |
| `body_markdown`     | TEXT                  |   no | comment content     |
| `status`            | `comment_status_enum` |   no | default `active`    |
| `depth`             | SMALLINT              |   no | default `0`         |
| `upvote_count`      | INTEGER               |   no | default `0`         |
| `downvote_count`    | INTEGER               |   no | default `0`         |
| `score`             | INTEGER               |   no | default `0`         |
| `rank_score`        | DOUBLE PRECISION      |   no | default `0`         |
| `created_at`        | TIMESTAMPTZ           |   no | default now()       |
| `updated_at`        | TIMESTAMPTZ           |   no | default now()       |


**Constraints**

- `depth >= 0`
- top-level comments have `parent_comment_id is null` and `depth = 0`
- replies should have `depth = parent.depth + 1`
- maximum depth is enforced in application logic; recommended max `6`

**Indexes**

- index on `post_id`
- index on `author_id`
- index on `parent_comment_id`
- composite index on (`post_id, created_at asc`)
- composite index on (`post_id, rank_score desc`)
- composite index on (`post_id, parent_comment_id`)

## 6.5 `post_votes`

| Column       | Type        | Null | Notes                                                    |
| ------------ | ----------- | ---: | -------------------------------------------------------- |
| `id`         | UUID        |   no | primary key                                              |
| `post_id`    | UUID        |   no | FK to `posts.id`                                         |
| `user_id`    | UUID        |   no | FK to `users.id`                                         |
| `vote_value` | SMALLINT    |   no | `1` or `-1`; if v1 is upvote-only, still keep extensible |
| `created_at` | TIMESTAMPTZ |   no | default now()                                            |
| `updated_at` | TIMESTAMPTZ |   no | default now()                                            |


**Constraints**

- unique `(post_id, user_id)`
- check `vote_value in (-1, 1)`

If v1 launches as upvote-only, application logic can simply never write `-1` while preserving future compatibility.

**Indexes**

- unique index on `(post_id, user_id)`
- index on `user_id`
- index on `post_id`

## 6.6 `comment_votes`

Store one user vote per comment.

| Column       | Type        | Null | Notes               |
| ------------ | ----------- | ---: | ------------------- |
| `id`         | UUID        |   no | primary key         |
| `comment_id` | UUID        |   no | FK to `comments.id` |
| `user_id`    | UUID        |   no | FK to `users.id`    |
| `vote_value` | SMALLINT    |   no | `1` or `-1`         |
| `created_at` | TIMESTAMPTZ |   no | default now()       |
| `updated_at` | TIMESTAMPTZ |   no | default now()       |


**Constraints**

- unique `(comment_id, user_id)`
- check `vote_value in (-1, 1)`

**Indexes**

- unique index on `(comment_id, user_id)`
- index on `user_id`
- index on `comment_id`

## 6.7 `flags`

Stores user-generated reports on posts, comments, or users.


| Column                | Type                    | Null | Notes                          |
| --------------------- | ----------------------- | ---: | ------------------------------ |
| `id`                  | UUID                    |   no | primary key                    |
| `target_type`         | `flag_target_type_enum` |   no | `post`, `comment`, `user`      |
| `target_id`           | UUID                    |   no | target object id               |
| `reporter_id`         | UUID                    |   no | FK to `users.id`               |
| `reason_code`         | `flag_reason_enum`      |   no | controlled moderation reason   |
| `notes`               | TEXT                    |  yes | optional free-text explanation |
| `status`              | `flag_status_enum`      |   no | default `open`                 |
| `reviewed_by_user_id` | UUID                    |  yes | FK to `users.id`, moderator    |
| `reviewed_at`         | TIMESTAMPTZ             |  yes | review timestamp               |
| `created_at`          | TIMESTAMPTZ             |   no | default now()                  |


**Constraints**

Recommended unique partial constraint:

- one reporter should not create duplicate open flags on same target for same reason

Possible uniqueness pattern:

- `(reporter_id, target_type, target_id, reason_code, status)` is tricky because status changes

- better enforce in application logic or use partial unique index on open states

**Indexes**

index on `(target_type, target_id)`
index on `reporter_id`
index on `status`
index on `created_at desc`


## 6.8 `moderation_actions`

Immutable audit log for moderator/admin actions.

**Columns**

| Column          | Type                          | Null | Notes                      |
| --------------- | ----------------------------- | ---: | -------------------------- |
| `id`            | UUID                          |   no | primary key                |
| `moderator_id`  | UUID                          |   no | FK to `users.id`           |
| `target_type`   | `moderation_target_type_enum` |   no | object class               |
| `target_id`     | UUID                          |   no | object id                  |
| `action_type`   | `moderation_action_type_enum` |   no | action performed           |
| `reason`        | TEXT                          |  yes | human-readable explanation |
| `metadata_json` | JSONB                         |  yes | arbitrary structured data  |
| `created_at`    | TIMESTAMPTZ                   |   no | default now()              |


**Notes**

This table should be append-only. Do not update rows except in rare migration scenarios.

**Indexes**

- index on `moderator_id`
- index on `(target_type, target_id)`
- index on `action_type`
- index on `created_at desc`


# 7. Ingestion Tables

## 7.1 sources

Represents external publishers, feeds, or ingestion origins.

| Column                  | Type                 | Null | Notes                         |
| ----------------------- | -------------------- | ---: | ----------------------------- |
| `id`                    | UUID                 |   no | primary key                   |
| `name`                  | VARCHAR(255)         |   no | source label                  |
| `source_type`           | `source_type_enum`   |   no | rss/manual/scraper/api        |
| `status`                | `source_status_enum` |   no | default `active`              |
| `url`                   | TEXT                 |   no | feed URL or source identifier |
| `site_url`              | TEXT                 |  yes | parent site                   |
| `default_category`      | `category_enum`      |  yes | default classification hint   |
| `domain_id`             | UUID                 |  yes | FK to `domains.id`            |
| `trust_score`           | NUMERIC(5,2)         |   no | default `1.00`                |
| `auto_publish`          | BOOLEAN              |   no | default `false`               |
| `poll_interval_minutes` | INTEGER              |   no | default `30`                  |
| `last_checked_at`       | TIMESTAMPTZ          |  yes | most recent poll              |
| `last_success_at`       | TIMESTAMPTZ          |  yes | most recent successful poll   |
| `last_error_at`         | TIMESTAMPTZ          |  yes | most recent failed poll       |
| `last_error_message`    | TEXT                 |  yes | diagnostic data               |
| `created_at`            | TIMESTAMPTZ          |   no | default now()                 |
| `updated_at`            | TIMESTAMPTZ          |   no | default now()                 |


**Constraints**

- `poll_interval_minutes > 0`
- `trust_score > 0`


**Indexes**

- index on `status`
- index on `auto_publish`
- index on `last_checked_at`
- index on `domain_id`


## 7.2 `ingestion_items`

Stores fetched candidate content from sources.

**Purpose**

This table provides:

- ingestion observability
- dedupe traceability
- approval workflows
- mapping from external source item to internal post

| Column                  | Type                    | Null | Notes                              |
| ----------------------- | ----------------------- | ---: | ---------------------------------- |
| `id`                    | UUID                    |   no | primary key                        |
| `source_id`             | UUID                    |   no | FK to `sources.id`                 |
| `external_id`           | VARCHAR(255)            |  yes | source-native item id if available |
| `title`                 | VARCHAR(300)            |   no | source item title                  |
| `url`                   | TEXT                    |   no | raw source URL                     |
| `url_normalized`        | TEXT                    |  yes | normalized for dedupe              |
| `published_at_external` | TIMESTAMPTZ             |  yes | source-published timestamp         |
| `discovered_at`         | TIMESTAMPTZ             |   no | first seen by system               |
| `ingestion_status`      | `ingestion_status_enum` |   no | current state                      |
| `detected_category`     | `category_enum`         |  yes | classifier guess                   |
| `linked_post_id`        | UUID                    |  yes | FK to `posts.id` if published      |
| `dedupe_match_post_id`  | UUID                    |  yes | FK to `posts.id` if duplicate      |
| `raw_payload_json`      | JSONB                   |  yes | original feed payload              |
| `processing_notes`      | TEXT                    |  yes | system/admin notes                 |
| `created_at`            | TIMESTAMPTZ             |   no | default now()                      |
| `updated_at`            | TIMESTAMPTZ             |   no | default now()                      |


**Constraints**

Possible uniqueness options:

- unique on `(source_id, external_id)` where `external_id is not null`
- do not rely only on source external ID; normalized URL is the stronger cross-source dedupe mechanism

**Indexes**

- index on `source_id`
- index on `ingestion_status`
- index on `published_at_external desc`
- index on `url_normalized`
- index on `linked_post_id`
- unique partial index on `(source_id, external_id)` where `external_id is not null`


# 8. Supporting Tables

These tables are not all equally critical, but they materially improve implementation quality.

## 8.1 `user_sessions`

Because v1 auth uses HTTP-only cookie sessions, a session table is recommended unless session state is stored entirely in another server-side session store.

**Suggested columns**

- `id`
- `user_id`
- `session_token_hash`
- `ip_address`
- `user_agent`
- `expires_at`
- `created_at`
- `last_seen_at`

This should be treated as a practical MVP table under the current auth direction.

## 8.2 `post_score_history`

Useful for observability and ranking tuning.

**Columns**

- `id`
- `post_id`
- `score`
- `rank_score`
- `upvote_count`
- `comment_count`
- `recorded_at`

This table is optional and should be sampled, not written on every single event if write volume becomes high.

## 8.3 `daily_stats`

Useful for admin dashboards and ecosystem metrics.

**Columns**

- `id`
- `date`
- `new_users`
- `new_posts`
- `new_comments`
- `new_votes`
- `active_users`
- `ingested_posts`
- `flag_count`
- `moderation_action_count`

# 9. Relationship Details

## 9.1 `users` → `posts`

- one-to-many
- deleting a user should not hard-delete authored posts
- safer approach: user status changes, content remains

## 9.2 `users` → `comments`

- one-to-many
- comment authorship remains even if user is suspended or banned

## 9.3 `posts` → `comments`

- one-to-many
- comments should be deleted only if post deletion policy requires hard purge; otherwise preserve under soft-delete rules

## 9.4 `domains` → `posts`

- one-to-many
- only non-text posts with URLs need a domain

## 9.5 `sources` → `ingestion_items`

- one-to-many
- used by ingestion workers for provenance

## 9.6 `ingestion_items` → `posts`

- optional one-to-one logical relation
- many ingestion items may dedupe to the same existing post, so technically:

  - `linked_post_id` is many-to-one
  - `dedupe_match_post_id` is many-to-one


# 10. Deletion Semantics

## 10.1 Users

Do not hard-delete users under normal operations.

Use:

- `status = suspended`
- `status = banned`

If legal/account deletion is required later, anonymization is safer than destructive cascading deletes.

## 10.2 Posts

Use `status` transitions:

- `active`
- `hidden`
- `removed`
- `locked`

Keep rows for audit and thread stability.

## 10.3 Comments

Same principle as posts.

A removed comment may render as:

> [removed]

while preserving child comments.

## 10.4 Votes

Votes can be hard-deleted when a user unvotes, since they are reversible interaction records and not core authored content. Audit logging can be added later if needed.

# 11. Counter and Aggregate Strategy

Hot feed products are read-heavy. Certain values should be denormalized.

## 11.1 Stored aggregates on `posts`

- `upvote_count`
- `comment_count`
- `score`
- `rank_score`

## 11.2 Stored aggregates on `comments`

- `upvote_count`
- `score`
- `rank_score`

## 11.3 Stored aggregates on `users`

- `karma`
- `post_count`
- `comment_count`

## 11.4 Consistency `model`

Recommended approach:

- write source-of-truth interaction row first
- update aggregates in same transaction where practical
- background reconciliation jobs can repair drift if needed

# 12. URL Normalization and Dedupe Storage

Because duplicate stories are fatal to feed quality, URL normalization matters.

## 12.1 `posts.url_normalized`

Should store canonicalized URL after:

- lowercase hostname
- removing known tracking parameters
- normalizing protocol where safe
- removing default ports
- trimming fragments when appropriate
- collapsing trailing slash inconsistencies

## 12.2 Why normalized URL is stored

This supports:

- duplicate prevention
- ingestion dedupe
- source analytics
- repost rules

## 12.3 Repost window policy

The schema should support a later rule such as:

- exact normalized URL cannot be re-posted for 30 days

This is primarily application logic. The partial unique index can help but should not rigidly prevent all future reposts forever unless that is desired.

# 13. Recommended Check Constraints

These should exist where feasible.

`posts`

- valid conditional fields by `post_type`
- `upvote_count >= 0`
- `downvote_count >= 0`
- `comment_count >= 0`

`comments`

- `depth >= 0`
- `upvote_count >= 0`
- `downvote_count >= 0`

`post_votes`

- `vote_value in (-1, 1)`

`comment_votes`

- `vote_value in (-1, 1)`

`domains`

- `trust_score > 0`

`sources`

- `poll_interval_minutes > 0`
- `trust_score > 0`

# 14. Recommended Foreign Key Behavior

## Suggested FK policies

- posts.author_id -> users.id
    - `ON DELETE RESTRICT`

- `posts.domain_id -> domains.id`

    - `ON DELETE SET NULL` is possible but generally avoid deleting domains

- `comments.post_id -> posts.id`

    - `ON DELETE CASCADE` only if posts are ever hard-deleted

    - otherwise keep standard FK and rely on soft-delete semantics

- `comments.parent_comment_id -> comments.id` 

    - ON DELETE SET NULL can break structure

    - better to preserve parents and use soft delete

- `post_votes.post_id -> posts.id`

    - `ON DELETE CASCADE`

- `post_votes.user_id -> users.id`

    - `ON DELETE CASCADE` or `RESTRICT` depending on user deletion strategy
    - since users are not normally hard-deleted, either is acceptable

- `comment_votes.comment_id -> comments.id`

    - `ON DELETE CASCADE`

- `flags.reporter_id -> users.id`

    - `ON DELETE RESTRICT`

- `moderation_actions.moderator_id -> users.id`

    - `ON DELETE RESTRICT`

# 15. Example DDL Sketches

These are illustrative, not final migration files.

Example: `users`


```SQL
create table users (
  id uuid primary key,
  username varchar(32) not null unique,
  email varchar(255) not null unique,
  password_hash text not null,
  bio text,
  role user_role_enum not null default 'user',
  status user_status_enum not null default 'active',
  karma integer not null default 0,
  post_count integer not null default 0,
  comment_count integer not null default 0,
  avatar_url text,
  last_active_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
```

Example: `posts`

```SQL
create table posts (
  id uuid primary key,
  author_id uuid not null references users(id),
  post_type post_type_enum not null,
  category category_enum not null,
  title varchar(300) not null,
  slug varchar(350) not null,
  url text,
  url_normalized text,
  domain_id uuid references domains(id),
  body_markdown text,
  status post_status_enum not null default 'active',
  is_ingested boolean not null default false,
  ingested_from_source_id uuid references sources(id),
  upvote_count integer not null default 0,
  downvote_count integer not null default 0,
  comment_count integer not null default 0,
  score integer not null default 0,
  rank_score double precision not null default 0,
  bookmark_count integer not null default 0,
  view_count integer not null default 0,
  submitted_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  last_commented_at timestamptz,
  job_expires_at timestamptz,
  check (
    (post_type = 'text' and body_markdown is not null and url is null and domain_id is null)
    or
    (post_type = 'link' and url is not null and url_normalized is not null and domain_id is not null)
    or
    (post_type = 'job' and (url is not null or body_markdown is not null))
  )
);
```

Example: `post_votes`

```SQL
create table post_votes (
  id uuid primary key,
  post_id uuid not null references posts(id) on delete cascade,
  user_id uuid not null references users(id),
  vote_value smallint not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (post_id, user_id),
  check (vote_value in (-1, 1))
);
```

# 16. Query Patterns the Schema Must Support

The schema is optimized for these hot paths.

## 16.1 Feed queries

Examples:

- get top active posts ordered by `rank_score desc`
- get newest posts by `submitted_at desc`
- get posts for category `ask`
- get active jobs not expired

## 16.2 Post detail queries

Examples:

- get post by `id`
- get author + domain + counts
- get comment tree for post

## 16.3 User profile queries

Examples:

- get recent submissions by user
- get recent comments by user
- get user karma and counts

## 16.4 Moderation queries

Examples:

- get open flags
- get actions on a post
- get suspicious domains

## 16.5 Ingestion queries

Examples:

- get active sources due for polling
- get ingestion items awaiting review
- find dedupe matches by normalized URL

# 17. Performance Notes

## 17.1 Why denormalized counters are justified

The homepage and post pages are read frequently. Calculating vote and comment counts from raw interaction tables on every request will become wasteful.

## 17.2 Why `rank_score` is stored

The top feed is a product-critical read path. Persisting rank score allows:

- cheaper ordering
- easier cache snapshot generation
- historical tuning

## 17.3 Why JSONB is limited

Use `JSONB` only where flexibility materially helps:

- `moderation_actions.metadata_json`
- `ingestion_items.raw_payload_json`

Do not use JSONB for core relational data like posts, votes, or comments.

# 18. Recommended Initial Decisions

To reduce ambiguity during implementation, the following defaults are recommended:

- primary keys: UUID
- votes schema supports both `1` and `-1`, even if UI launches as upvote-only
- one `posts` table for all top-level content
- one primary category per post in v1
- soft delete/status transitions for posts and comments
- denormalized counts stored on hot entities
- domain trust as a first-class table concern
- ingestion provenance stored explicitly
- richer ingestion lifecycle states are persisted where they provide operator value
- `disabled` source status acts as the operationally blocked state
- flag reasons use a controlled enum
- `user_sessions` is part of the practical MVP schema
- route posts by `id + slug`, not slug only


# 19. Summary

This schema is designed for a feed-first, discussion-heavy platform where:

- `posts` are the primary ranked objects
- `comments` form the discussion layer
- `votes` shape visibility
- `domains` and `sources` support trust and ingestion
- `flags` and `moderation_actions` preserve quality and auditability

The most important design choice is keeping the schema centered on a strong posts table, explicit interaction tables, and first-class moderation and ingestion support. This gives the platform a clean path from MVP into a more sophisticated ecosystem intelligence product without requiring a major data-model rewrite.
