# Phase 2 Manual Review And Test Checklist

## Purpose

This checklist is the manual review and validation pass for Phase 2.

Use it before starting Phase 3.

The goal is to confirm that:

- the database layer is understandable
- the local development workflow is stable
- migrations are trustworthy
- schema rules match the planned Phase 2 intent
- the API still boots cleanly on top of the new persistence layer

This document complements:

- `docs/agent-review/PHASE2_DATABASE_PLAN.md`
- `docs/agent-review/DEVELOPMENT_TEST_CHECKPOINTS.md`

## Scope

This checklist covers:

- file review
- env and local workflow review
- Docker Postgres review
- migration validation
- schema inspection
- manual constraint testing
- API boot and health verification

It does not cover:

- auth flows
- session issuance
- CSRF
- feed endpoints
- frontend product features
- worker jobs using the database

## Before You Start

Make sure you are in the repo root.

Make sure these exist:

- `.env`
- `compose.yaml`
- local `pgAdmin`

If `.env` is missing:

```bash
cp .env.example .env
```

Then edit `.env` before running the services.
Runtime config should come from `.env`, not `.env.example`.

Install dependencies:

```bash
npm install
uv sync --all-packages
```

## Review Order

Review in this order.

### 1. Root workflow and config

Read:

- `package.json`
- `.env.example`
- `.env`
- `compose.yaml`
- `README.md`
- `COMMANDS.md`

What to verify:

- the root scripts match the intended workflow
- `.env.example` contains placeholders only
- `.env` is the real runtime file
- Docker only provisions Postgres for now
- docs match the actual command surface

### 2. Shared backend config

Read:

- `packages/backend/src/rifthub_backend/config.py`
- `packages/backend/src/rifthub_backend/__init__.py`
- `packages/backend/pyproject.toml`

What to verify:

- `.env` loading is explicit and predictable
- DB URLs come from env, not hardcoded runtime assumptions
- settings shape is still small and understandable
- dependencies added in Phase 2 are justified

### 3. Shared DB primitives

Read:

- `packages/backend/src/rifthub_backend/db/base.py`
- `packages/backend/src/rifthub_backend/db/session.py`
- `packages/backend/src/rifthub_backend/db/types.py`

What to verify:

- SQLAlchemy naming conventions are explicit
- the async engine/session lifecycle is coherent
- engine and session-factory cache reuse is safe:
  - same effective DB config may reuse the cache
  - different effective DB config must fail loudly unless `dispose_engine()` was called first
- API startup can fail fast on broken DB connectivity via an explicit ping
- enum values match `docs/DATABASE_SCHEMA.md`
- `dispose_engine()` exists and is used to clean up on shutdown

### 4. Model review

Read:

- `packages/backend/src/rifthub_backend/models/__init__.py`
- `packages/backend/src/rifthub_backend/models/user.py`
- `packages/backend/src/rifthub_backend/models/domain.py`
- `packages/backend/src/rifthub_backend/models/source.py`
- `packages/backend/src/rifthub_backend/models/post.py`
- `packages/backend/src/rifthub_backend/models/comment.py`
- `packages/backend/src/rifthub_backend/models/vote.py`
- `packages/backend/src/rifthub_backend/models/flag.py`
- `packages/backend/src/rifthub_backend/models/moderation.py`
- `packages/backend/src/rifthub_backend/models/ingestion.py`
- `packages/backend/src/rifthub_backend/models/session.py`

What to verify:

- table ownership matches the schema doc
- defaults are sensible
- constraints are attached to the right tables
- partial indexes exist where intended
- relationship directions make sense
- JSONB use is limited to where it was planned

### 5. API integration

Read:

- `apps/api/src/rifthub_api/main.py`
- `apps/api/pyproject.toml`

What to verify:

- the API still stays thin
- startup initializes shared resources and pings the DB before serving
- shutdown disposes the DB engine
- `/health` is treated as a shallow liveness check, not DB readiness
- Alembic dependency is present

### 6. Migration layer

Read:

- `apps/api/alembic.ini`
- `apps/api/alembic/env.py`
- `apps/api/alembic/script.py.mako`
- `apps/api/alembic/versions/20260313_01_initial_schema.py`

What to verify:

- Alembic loads metadata from the shared backend package
- the migration URL comes from shared settings
- the initial revision is in sync with the current model constraints
- enum creation is explicit
- upgrade and downgrade order are reasonable

### 7. Tests

Read:

- `apps/api/tests/test_health.py`
- `apps/api/tests/test_config.py`
- `apps/api/tests/test_db_session.py`
- `apps/api/tests/test_schema_metadata.py`

What to verify:

- current tests cover config loading
- current tests cover config defaults and boolean parsing
- current tests cover DB engine/session cache lifecycle and reconfiguration guards
- current tests cover startup/shutdown lifespan behavior around DB ping and engine disposal
- current tests cover schema metadata shape
- current tests do not pretend to cover full DB integration yet

## Manual Test Flow

Run the steps in order.

### Step 1. Start local Postgres

```bash
npm run db:up
npm run db:logs
```

Expected result:

- the `postgres` container starts
- logs show the database is ready to accept connections

If you do not want the log stream to block your terminal, open it in a separate terminal tab.

### Step 2. Confirm `.env` values are the ones you expect

Inspect:

- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `RIFTHUB_DATABASE_URL`
- `RIFTHUB_MIGRATION_DATABASE_URL`

Expected result:

- URLs point to your local Postgres
- database name is `rifthub`
- credentials match the Docker config

### Step 3. Run the automated Phase 2 tests

```bash
npm run api:test
```

Expected result:

- all tests pass

Current expected pass count:

- `26 passed`

### Step 4. Validate the migration SQL renders

```bash
uv run --package rifthub-api alembic -c apps/api/alembic.ini upgrade head --sql
```

Expected result:

- SQL renders successfully
- no import errors
- no enum-generation failures

You do not need to read every line.
Spot-check that it includes:

- enum creation
- table creation
- indexes
- user/domain/post counter constraints
- post ingestion coherence constraint
- comment self-parent and same-post parent integrity constraints
- flag review-state coherence constraint
- insert into `alembic_version`

### Step 5. Apply the migration to the local database

```bash
npm run db:upgrade
```

Expected result:

- migration completes without error

Important:

- if you have another local Postgres server installed, such as Postgres.app, make sure it is not also bound to `127.0.0.1:5432`
- this manual flow assumes the Docker container is the only Postgres server listening on the configured host port
- if `psql` or pgAdmin show a different database list than Alembic/migrations expect, check for a port conflict before assuming the migration failed

### Step 6. Check tables with `psql`

```bash
psql "postgresql://postgres:postgres@127.0.0.1:5432/rifthub" -c '\dt'
```

Expected result:

- `users`
- `domains`
- `sources`
- `posts`
- `comments`
- `post_votes`
- `comment_votes`
- `flags`
- `moderation_actions`
- `ingestion_items`
- `user_sessions`
- `alembic_version`

Also verify:

```bash
psql "postgresql://postgres:postgres@127.0.0.1:5432/rifthub" -c "select version_num from alembic_version;"
```

Expected result:

- `20260313_01`

### Step 7. Inspect the schema visually in pgAdmin

In pgAdmin, connect to the local `rifthub` database and manually inspect:

- Schemas
- Tables
- Columns
- Indexes
- Constraints
- Types

Check specifically:

- enum types exist
- foreign keys look correct
- partial indexes exist on:
  - `flags`
  - `ingestion_items`
- JSONB columns exist only on:
  - `moderation_actions.metadata_json`
  - `ingestion_items.raw_payload_json`

If pgAdmin does not show `rifthub` under `Databases`:

- confirm it is connected to the same server/port as the working host `psql` DSN above
- run `select datname from pg_database order by datname;` in pgAdmin Query Tool
- if `rifthub` is missing there, pgAdmin is connected to the wrong Postgres server
- the most common cause is a local Postgres installation still listening on `5432`

### Step 8. Verify enum types directly

Run:

```bash
psql -d rifthub -c "SELECT typname FROM pg_type WHERE typname IN ('user_role_enum','user_status_enum','post_type_enum','post_status_enum','comment_status_enum','category_enum','flag_target_type_enum','flag_status_enum','flag_reason_enum','moderation_target_type_enum','moderation_action_type_enum','source_type_enum','source_status_enum','ingestion_status_enum') ORDER BY typname;"
```

Expected result:

- all 14 enum type names are returned

### Step 9. Verify indexes directly

Run:

```bash
psql -d rifthub -c "SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename, indexname;"
```

Expected result:

- indexes exist for the major feed, comments, votes, moderation, and ingestion lookup paths

Pay special attention to:

- `uq_post_votes_post_id_user_id`
- `uq_comment_votes_comment_id_user_id`
- `uq_flags_open_reporter_target_reason`
- `uq_ingestion_items_source_id_external_id`

## Manual Data Validation

Use the following tests in `psql` or pgAdmin Query Tool.

For each test:

- begin a transaction
- run the test
- verify success or failure
- roll back

This keeps your local DB clean.

### Test A. Valid base inserts succeed

```sql
BEGIN;

INSERT INTO users (
  id, username, email, password_hash
) VALUES (
  '11111111-1111-1111-1111-111111111111',
  'alice_dev',
  'alice@example.com',
  'hashed'
);

INSERT INTO domains (
  id, hostname
) VALUES (
  '22222222-2222-2222-2222-222222222222',
  'example.com'
);

INSERT INTO sources (
  id, name, source_type, url, domain_id
) VALUES (
  '33333333-3333-3333-3333-333333333333',
  'Example Feed',
  'rss',
  'https://example.com/feed.xml',
  '22222222-2222-2222-2222-222222222222'
);

INSERT INTO posts (
  id, author_id, post_type, category, title, slug, url, url_normalized, domain_id, submitted_at
) VALUES (
  '44444444-4444-4444-4444-444444444444',
  '11111111-1111-1111-1111-111111111111',
  'link',
  'launch',
  'Example Post',
  'example-post',
  'https://example.com/post',
  'https://example.com/post',
  '22222222-2222-2222-2222-222222222222',
  now()
);

INSERT INTO comments (
  id, post_id, author_id, body_markdown
) VALUES (
  '55555555-5555-5555-5555-555555555555',
  '44444444-4444-4444-4444-444444444444',
  '11111111-1111-1111-1111-111111111111',
  'first comment'
);

INSERT INTO post_votes (
  id, post_id, user_id, vote_value
) VALUES (
  '66666666-6666-6666-6666-666666666666',
  '44444444-4444-4444-4444-444444444444',
  '11111111-1111-1111-1111-111111111111',
  1
);

INSERT INTO comment_votes (
  id, comment_id, user_id, vote_value
) VALUES (
  '77777777-7777-7777-7777-777777777777',
  '55555555-5555-5555-5555-555555555555',
  '11111111-1111-1111-1111-111111111111',
  1
);

ROLLBACK;
```

Expected result:

- all inserts succeed

### Test B. Duplicate username fails

```sql
BEGIN;

INSERT INTO users (id, username, email, password_hash)
VALUES ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'duplicate_user', 'one@example.com', 'hashed');

INSERT INTO users (id, username, email, password_hash)
VALUES ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'duplicate_user', 'two@example.com', 'hashed');

ROLLBACK;
```

Expected result:

- the second insert fails on unique username

### Test C. Duplicate email fails

```sql
BEGIN;

INSERT INTO users (id, username, email, password_hash)
VALUES ('cccccccc-cccc-cccc-cccc-cccccccccccc', 'user_one', 'dup@example.com', 'hashed');

INSERT INTO users (id, username, email, password_hash)
VALUES ('dddddddd-dddd-dddd-dddd-dddddddddddd', 'user_two', 'dup@example.com', 'hashed');

ROLLBACK;
```

Expected result:

- the second insert fails on unique email

### Test D. Invalid vote value fails

```sql
BEGIN;

INSERT INTO users (id, username, email, password_hash)
VALUES ('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 'vote_user', 'vote@example.com', 'hashed');

INSERT INTO domains (id, hostname)
VALUES ('ffffffff-ffff-ffff-ffff-ffffffffffff', 'vote-example.com');

INSERT INTO posts (
  id, author_id, post_type, category, title, slug, url, url_normalized, domain_id, submitted_at
) VALUES (
  '12121212-1212-1212-1212-121212121212',
  'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
  'link',
  'launch',
  'Vote Target',
  'vote-target',
  'https://vote-example.com/item',
  'https://vote-example.com/item',
  'ffffffff-ffff-ffff-ffff-ffffffffffff',
  now()
);

INSERT INTO post_votes (id, post_id, user_id, vote_value)
VALUES (
  '13131313-1313-1313-1313-131313131313',
  '12121212-1212-1212-1212-121212121212',
  'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
  2
);

ROLLBACK;
```

Expected result:

- the vote insert fails on check constraint

### Test E. Duplicate post vote fails

```sql
BEGIN;

INSERT INTO users (id, username, email, password_hash)
VALUES ('14141414-1414-1414-1414-141414141414', 'vote_dup_user', 'vote_dup@example.com', 'hashed');

INSERT INTO domains (id, hostname)
VALUES ('15151515-1515-1515-1515-151515151515', 'vote-dup.com');

INSERT INTO posts (
  id, author_id, post_type, category, title, slug, url, url_normalized, domain_id, submitted_at
) VALUES (
  '16161616-1616-1616-1616-161616161616',
  '14141414-1414-1414-1414-141414141414',
  'link',
  'launch',
  'Dup Vote Target',
  'dup-vote-target',
  'https://vote-dup.com/item',
  'https://vote-dup.com/item',
  '15151515-1515-1515-1515-151515151515',
  now()
);

INSERT INTO post_votes (id, post_id, user_id, vote_value)
VALUES ('17171717-1717-1717-1717-171717171717', '16161616-1616-1616-1616-161616161616', '14141414-1414-1414-1414-141414141414', 1);

INSERT INTO post_votes (id, post_id, user_id, vote_value)
VALUES ('18181818-1818-1818-1818-181818181818', '16161616-1616-1616-1616-161616161616', '14141414-1414-1414-1414-141414141414', -1);

ROLLBACK;
```

Expected result:

- the second vote insert fails on unique index

### Test F. Invalid text post fails if URL fields are set

```sql
BEGIN;

INSERT INTO users (id, username, email, password_hash)
VALUES ('19191919-1919-1919-1919-191919191919', 'text_user', 'text@example.com', 'hashed');

INSERT INTO domains (id, hostname)
VALUES ('20202020-2020-2020-2020-202020202020', 'text-invalid.com');

INSERT INTO posts (
  id, author_id, post_type, category, title, slug, url, url_normalized, domain_id, body_markdown, submitted_at
) VALUES (
  '21212121-2121-2121-2121-212121212121',
  '19191919-1919-1919-1919-191919191919',
  'text',
  'ask',
  'Invalid Text Post',
  'invalid-text-post',
  'https://text-invalid.com/item',
  'https://text-invalid.com/item',
  '20202020-2020-2020-2020-202020202020',
  'body',
  now()
);

ROLLBACK;
```

Expected result:

- insert fails on the `text` post check constraint

### Test G. Invalid link post fails if required URL fields are missing

```sql
BEGIN;

INSERT INTO users (id, username, email, password_hash)
VALUES ('23232323-2323-2323-2323-232323232323', 'link_user', 'link@example.com', 'hashed');

INSERT INTO posts (
  id, author_id, post_type, category, title, slug, submitted_at
) VALUES (
  '24242424-2424-2424-2424-242424242424',
  '23232323-2323-2323-2323-232323232323',
  'link',
  'launch',
  'Invalid Link Post',
  'invalid-link-post',
  now()
);

ROLLBACK;
```

Expected result:

- insert fails on the `link` post check constraint

### Test H. Invalid source polling interval fails

```sql
BEGIN;

INSERT INTO sources (
  id, name, source_type, url, poll_interval_minutes
) VALUES (
  '25252525-2525-2525-2525-252525252525',
  'Bad Poll Source',
  'rss',
  'https://bad-source.example/feed.xml',
  0
);

ROLLBACK;
```

Expected result:

- insert fails on the source poll interval check

### Test I. Ingestion external ID uniqueness works per source

```sql
BEGIN;

INSERT INTO domains (id, hostname)
VALUES ('26262626-2626-2626-2626-262626262626', 'ingest-example.com');

INSERT INTO sources (
  id, name, source_type, url, domain_id
) VALUES (
  '27272727-2727-2727-2727-272727272727',
  'Ingest Source',
  'rss',
  'https://ingest-example.com/feed.xml',
  '26262626-2626-2626-2626-262626262626'
);

INSERT INTO ingestion_items (
  id, source_id, external_id, title, url, discovered_at, ingestion_status
) VALUES (
  '28282828-2828-2828-2828-282828282828',
  '27272727-2727-2727-2727-272727272727',
  'ext-1',
  'Item One',
  'https://ingest-example.com/one',
  now(),
  'discovered'
);

INSERT INTO ingestion_items (
  id, source_id, external_id, title, url, discovered_at, ingestion_status
) VALUES (
  '29292929-2929-2929-2929-292929292929',
  '27272727-2727-2727-2727-272727272727',
  'ext-1',
  'Item Two',
  'https://ingest-example.com/two',
  now(),
  'discovered'
);

ROLLBACK;
```

Expected result:

- the second insert fails on the partial unique index

## API Runtime Checks

### Step 10. Start the API

```bash
npm run api:dev
```

Expected result:

- the service boots successfully
- startup logs mention the environment
- the API does not crash because of the DB layer import path

### Step 11. Check the health endpoint

In another terminal:

```bash
curl http://127.0.0.1:8000/health
```

Expected result:

```json
{"service":"api","status":"ok","environment":"development"}
```

### Step 12. Stop the API cleanly

Use `Ctrl+C`.

Expected result:

- the process stops without tracebacks
- shutdown completes cleanly

## Downgrade Validation

This is destructive for the local dev schema.
Only run it when you are okay dropping the Phase 2 tables from the local database.

### Step 13. Downgrade to base

```bash
uv run --package rifthub-api alembic -c apps/api/alembic.ini downgrade base
```

Expected result:

- downgrade completes without error

### Step 14. Confirm app tables are gone

```bash
psql -d rifthub -c '\dt'
```

Expected result:

- the Phase 2 app tables are gone
- depending on Alembic behavior, `alembic_version` may be absent or remain empty

### Step 15. Re-apply the migration

```bash
npm run db:upgrade
```

Expected result:

- the schema is recreated cleanly

## Exit Criteria

You should not start Phase 3 until all of these are true:

- file review is complete
- `npm run api:test` passes
- Docker Postgres starts reliably
- migration SQL renders
- `upgrade head` succeeds
- the expected tables exist
- enum types exist
- core constraints fail on bad data
- API starts successfully
- `/health` returns successfully
- downgrade and re-upgrade both work on the local dev database

## Notes To Record During Review

As you review, write down:

- any schema mismatch against `docs/DATABASE_SCHEMA.md`
- any constraint that feels too weak or too rigid
- any naming convention you want changed now before Phase 3
- any migration behavior that feels unsafe
- any local workflow pain around `.env`, Docker, pgAdmin, or Alembic

Those are the right things to resolve before API feature work begins.
