# REPOSITORY_STRUCTURE.md

## Project
**Working name:** RiftHub  
**System type:** Community-ranked discussion and discovery platform for African tech

---

# 1. Purpose

This document defines the repository layout for the project.

Its purpose is to translate the architecture and service-boundary decisions into a codebase structure that is:

- easy to navigate
- modular
- scalable
- production-oriented
- friendly to solo development now and team growth later

A good repository structure prevents confusion long before infrastructure scale becomes a problem.

---

# 2. Repository Strategy

This project should use a **monorepo**.

That is the right choice because the system has multiple tightly related parts:

- frontend
- backend API
- worker processes
- shared docs
- shared contracts/types where useful

A monorepo keeps these parts versioned together, which is valuable early when the product surface and data contracts are still evolving quickly.

---

# 3. Top-Level Layout

Recommended top-level structure:

```text
rifthub/
  apps/
    web/
    api/
    worker/
  packages/
    config/
    types/
    ui/                # optional later
  docs/
  scripts/
  infra/
  .github/
  .env.example
  README.md
  pnpm-workspace.yaml  # if using pnpm workspace
```

4. Why This Structure
4.1 apps/

Contains independently runnable applications.

This is where deployed runtime surfaces live.

Recommended apps:

web → Next.js frontend

api → FastAPI backend

worker → background jobs / ingestion / ranking refresh

4.2 packages/

Contains reusable shared packages.

These should remain small and intentional.

Good uses:

shared TypeScript types

shared lint/format config

shared design tokens later

shared utility contracts

Do not force heavy premature sharing.

4.3 docs/

Contains architecture, policies, and operational documents.

This repo already justifies a serious docs folder because the product has meaningful domain complexity.

4.4 scripts/

Contains developer and ops helper scripts.

Examples:

local DB setup

seed scripts

migration helpers

feed fixture import

user bootstrap scripts

4.5 infra/

Contains deployment and infrastructure-related definitions.

Examples:

Dockerfiles

Railway configs

environment examples

infrastructure notes

future IaC if added

4.6 .github/

Contains CI/CD automation.

Examples:

lint/test workflows

migration verification

deploy checks

PR templates

issue templates

5. Recommended Detailed Structure
5.1 Root
rifthub/
  apps/
  packages/
  docs/
  scripts/
  infra/
  .github/
  .env.example
  .gitignore
  README.md
Root file purposes
File	Purpose
README.md	project overview and setup
.env.example	environment template
.gitignore	ignore build/cache/secrets
workspace config	monorepo tooling
5.2 apps/web — Frontend
apps/
  web/
    app/
    components/
    lib/
    hooks/
    styles/
    public/
    tests/
    package.json
    tsconfig.json
    next.config.ts
5.2.1 app/

Next.js App Router structure.

Recommended:

app/
  (public)/
    page.tsx
    new/
      page.tsx
    ask/
      page.tsx
    show/
      page.tsx
    jobs/
      page.tsx
    post/
      [id]/
        [slug]/
          page.tsx
    user/
      [username]/
        page.tsx
  (auth)/
    login/
      page.tsx
    register/
      page.tsx
  (dashboard)/
    moderation/
      page.tsx
    admin/
      page.tsx
  layout.tsx
  globals.css
Why this route grouping works

public browsing is separated from auth surfaces

moderator/admin views are isolated

feed routes stay obvious

canonical post and profile paths are easy to find

5.2.2 components/

UI components should be grouped by domain, not by arbitrary technical labels only.

Recommended:

components/
  layout/
    Header.tsx
    Footer.tsx
    Shell.tsx
  feed/
    FeedList.tsx
    FeedItem.tsx
    CategoryBadge.tsx
    VoteButton.tsx
  post/
    PostHeader.tsx
    PostMeta.tsx
    PostBody.tsx
  comments/
    CommentList.tsx
    CommentItem.tsx
    CommentForm.tsx
  auth/
    LoginForm.tsx
    RegisterForm.tsx
  moderation/
    FlagQueue.tsx
    ModerationActions.tsx
  admin/
    SourceTable.tsx
    IngestionQueue.tsx
  shared/
    EmptyState.tsx
    ErrorState.tsx
    Pagination.tsx
Important rule

Avoid giant components/ui dumping grounds for business components. Keep reusable primitive UI separate only if it is truly generic.

5.2.3 lib/

Frontend support code.

Recommended:

lib/
  api/
    client.ts
    feeds.ts
    posts.ts
    comments.ts
    auth.ts
    moderation.ts
    admin.ts
  auth/
    session.ts
    csrf.ts
    guards.ts
  utils/
    formatDate.ts
    formatScore.ts
    slug.ts
  constants/
    categories.ts
    routes.ts
  types/
    api.ts
    domain.ts
Rule

lib/api should map closely to backend API surfaces.

5.2.4 hooks/

Only for real reusable React hooks.

Examples:

hooks/
  useCurrentUser.ts
  useVote.ts
  useInfiniteFeed.ts

Do not dump ordinary helper logic here.

5.2.5 tests/

Frontend-focused tests.

tests/
  components/
  pages/
  integration/

If you later use Playwright, end-to-end tests can live here or in a separate root folder.

5.3 apps/api — Backend API
apps/
  api/
    app/
    tests/
    alembic/
    pyproject.toml
    alembic.ini
    Dockerfile
5.3.1 app/

Recommended backend application structure:

app/
  api/
    deps/
    routes/
  core/
  db/
  schemas/
  services/
  workers/
  utils/
  main.py
5.3.2 app/api/

HTTP layer only.

api/
  deps/
    auth.py
    csrf.py
    db.py
    permissions.py
  routes/
    auth.py
    users.py
    feeds.py
    posts.py
    comments.py
    votes.py
    flags.py
    moderation.py
    admin_sources.py
    admin_ingestion.py
Rule

Route files should stay thin:

parse request

call service

serialize response

map errors

Business logic should not live here.

5.3.3 app/core/

Application-wide foundational concerns.

core/
  config.py
  security.py
  logging.py
  constants.py
  exceptions.py

Purpose:

environment parsing

security helpers

structured logging setup

global constants

exception types

5.3.4 app/db/

Persistence layer.

db/
  session.py
  base.py
  models/
    user.py
    domain.py
    post.py
    comment.py
    vote.py
    flag.py
    moderation.py
    source.py
    ingestion_item.py
Notes

base.py defines declarative base

session.py manages DB session lifecycle

each major model gets its own file for clarity

5.3.5 app/schemas/

Pydantic models for request/response validation.

schemas/
  auth.py
  users.py
  posts.py
  comments.py
  votes.py
  feeds.py
  flags.py
  moderation.py
  sources.py
  ingestion.py
  common.py
Rule

These are transport schemas, not ORM models.

5.3.6 app/services/

This is the heart of the backend.

Recommended structure:

services/
  auth/
    service.py
  users/
    service.py
  posts/
    service.py
    validators.py
    slugging.py
  comments/
    service.py
    validators.py
  votes/
    service.py
  feeds/
    service.py
    cache.py
  ranking/
    service.py
    formulas.py
    config.py
  moderation/
    service.py
    actions.py
  ingestion/
    service.py
    polling.py
    parsing.py
    normalization.py
    dedupe.py
    publishing.py
  domains/
    service.py
Why this matters

This structure enforces service boundaries.

Each domain owns:

rules

writes

orchestration

5.3.7 app/workers/

Worker-entry code that may be shared or invoked by the dedicated worker app.

Examples:

workers/
  jobs/
    refresh_feed_scores.py
    poll_sources.py
    reconcile_counts.py
    expire_jobs.py
  scheduler.py

If you prefer strict separation, worker runtime code can live mostly in apps/worker, with shared logic staying in services/.

5.3.8 app/utils/

Small helpers with no strong domain ownership.

Examples:

utils/
  time.py
  text.py
  urls.py
  hashing.py

Keep this folder tight. It should not become a dumping ground.

5.3.9 tests/

Backend tests should mirror domain boundaries.

tests/
  unit/
    auth/
    posts/
    comments/
    votes/
    ranking/
    ingestion/
    moderation/
  integration/
    api/
    db/
  fixtures/
    factories/
    seed_data/
5.3.10 alembic/

Database migration directory.

alembic/
  versions/

Migration discipline matters. Every schema change goes here.

5.4 apps/worker — Background Worker
apps/
  worker/
    worker/
      jobs/
      runners/
      main.py
    tests/
    pyproject.toml
    Dockerfile
5.4.1 Purpose

The worker app should handle:

source polling

ingestion processing

score recomputation

cache warming

reconciliation tasks

periodic cleanup

5.4.2 Recommended structure
worker/
  jobs/
    poll_sources.py
    normalize_ingestion_items.py
    publish_ingestion_items.py
    recompute_post_scores.py
    refresh_feed_snapshots.py
    reconcile_aggregates.py
    expire_job_posts.py
  runners/
    scheduler.py
    queue_runner.py
  main.py
Rule

Worker app should contain runtime orchestration, while shared business logic should live in apps/api/app/services/...

That prevents duplicate domain logic across apps.

5.5 packages/config

Reusable configuration presets.

Examples:

packages/
  config/
    eslint/
    prettier/
    typescript/

If this feels premature, start small. But centralized config often pays off quickly.

5.6 packages/types

Useful if you want shared frontend TypeScript types derived from API contracts.

packages/
  types/
    src/
      api.ts
      domain.ts
    package.json
Important note

Do not over-share too early. Shared types are useful, but backend remains source of truth.

5.7 docs

This folder should contain the documents already created.

Current practical structure:

```text
docs/
  ARCHITECTURE.md
  DATABASE_SCHEMA.md
  API_SPEC.md
  RANKING_SYSTEM.md
  INGESTION_PIPELINE.md
  MODERATION_POLICY.md
  SYSTEM_ARCHITECTURE.md
  SERVICE_BOUNDARIES.md
  REPO_STRUCTURE.md
  MVP_SCOPE.md
  ROADMAP.md
  SECURITY.md
  TESTING_STRATEGY.md
  Qs.md
  agent-review/
    MEMORY.md
    REVIEW_ORDER.md
    *_REVIEW.md
```

Keep the main planning docs flat during the docs-review stage to avoid churn while references are still being normalized. The `agent-review/` folder holds review notes, open questions, and working memory.

5.8 scripts

Recommended contents:

scripts/
  bootstrap.sh
  dev-web.sh
  dev-api.sh
  dev-worker.sh
  seed-dev-data.py
  reset-local-db.sh
  backfill-ingestion.py

These help avoid repetitive local setup steps.

5.9 infra

Recommended contents:

infra/
  railway/
    api.md
    worker.md
  vercel/
    web.md
  docker/
    api.Dockerfile
    worker.Dockerfile
  env/
    development.env.example
    staging.env.example
    production.env.example

This can later evolve into Terraform or other IaC if needed.

5.10 .github

Recommended structure:

.github/
  workflows/
    web-ci.yml
    api-ci.yml
    worker-ci.yml
    migrations-check.yml
  ISSUE_TEMPLATE/
  PULL_REQUEST_TEMPLATE.md
6. Workspace Tooling Recommendations

If using a monorepo with Next.js and shared TS packages, a JS workspace tool is helpful.

Recommended options:

pnpm workspaces

turbo later if build orchestration becomes useful

A practical setup:

use pnpm for workspace management

add Turbo only if builds/test orchestration becomes meaningfully complex

Do not overcomplicate tooling at the start.

7. Language Boundary Notes

This repo is polyglot:

frontend: TypeScript

backend: Python

worker: Python

This is acceptable. It mirrors the actual architecture cleanly.

Important rule:

keep shared contracts documented first

do not try to force runtime code sharing across TS and Python

share concepts, schemas, and generated types where useful, not core logic

8. Example Full Tree

A more complete example:

rifthub/
  apps/
    web/
      app/
        (public)/
          page.tsx
          new/page.tsx
          ask/page.tsx
          show/page.tsx
          jobs/page.tsx
          post/[id]/[slug]/page.tsx
          user/[username]/page.tsx
        (auth)/
          login/page.tsx
          register/page.tsx
        (dashboard)/
          moderation/page.tsx
          admin/page.tsx
        layout.tsx
        globals.css
      components/
        layout/
        feed/
        post/
        comments/
        auth/
        moderation/
        admin/
        shared/
      lib/
        api/
        auth/
        constants/
        types/
        utils/
      hooks/
      tests/
      package.json
      tsconfig.json
      next.config.ts

    api/
      app/
        api/
          deps/
          routes/
        core/
        db/
          models/
        schemas/
        services/
          auth/
          users/
          posts/
          comments/
          votes/
          feeds/
          ranking/
          moderation/
          ingestion/
          domains/
        workers/
        utils/
        main.py
      tests/
        unit/
        integration/
        fixtures/
      alembic/
        versions/
      pyproject.toml
      alembic.ini
      Dockerfile

    worker/
      worker/
        jobs/
        runners/
        main.py
      tests/
      pyproject.toml
      Dockerfile

  packages/
    config/
    types/

  docs/
    ARCHITECTURE.md
    DATABASE_SCHEMA.md
    API_SPEC.md
    RANKING_SYSTEM.md
    INGESTION_PIPELINE.md
    MODERATION_POLICY.md
    SYSTEM_ARCHITECTURE.md
    SERVICE_BOUNDARIES.md
    REPO_STRUCTURE.md
    MVP_SCOPE.md
    ROADMAP.md
    SECURITY.md
    TESTING_STRATEGY.md
    Qs.md
    agent-review/

  scripts/
    bootstrap.sh
    seed-dev-data.py

  infra/
    railway/
    vercel/
    env/

  .github/
    workflows/

  .env.example
  .gitignore
  README.md
  pnpm-workspace.yaml
9. Naming Conventions

Consistency matters.

9.1 Files

Use:

snake_case.py in Python

PascalCase.tsx for React components

kebab-case only where framework conventions strongly favor it

9.2 Routes

API route files should map to domain surfaces clearly.

Examples:

posts.py

comments.py

moderation.py

admin_ingestion.py

Avoid vague files like:

utils.py

helpers.py

misc.py

at major domain levels.

9.3 Service modules

Prefer one service module per domain area.

Examples:

services/posts/service.py

services/votes/service.py

services/ranking/formulas.py

This makes ownership obvious.

10. Repo Discipline Rules

These rules will keep the repo healthy.

10.1 Do not mix frontend and backend logic

API behavior belongs in apps/api, not in Next.js server components pretending to be business services.

10.2 Do not bypass services for domain writes

If the ingestion worker needs to create a post, it should go through post-domain service logic, not direct raw table insertion.

10.3 Keep docs current with code

If ranking formula changes materially, update:

RANKING_SYSTEM.md

relevant service code

tests

Architecture drift is dangerous.

10.4 Avoid generic utility sprawl

Do not create giant utils/ folders full of unrelated logic.

If a utility has a clear domain owner, keep it near that domain.

10.5 Separate tests by level

Distinguish:

unit tests

integration tests

end-to-end tests

This makes failures easier to reason about.

11. Suggested Repo Bootstrap Order

Use the repo structure to guide implementation.

This section is about codebase setup order, not the authoritative product roadmap phases.

Phase 1

Set up:

apps/web

apps/api

root docs

root env templates

Phase 2

Implement backend foundations:

DB models

Alembic

auth

posts/comments/votes services

API routes

Phase 3

Implement frontend feed surfaces:

top feed

new feed

post page

submit flows

auth pages

Phase 4

Add worker jobs and runtime orchestration:

score refresh

ingestion polling

cache refresh

Phase 5

Add ranking and feed-refresh implementation:

rank score recomputation

feed snapshot refresh

cache invalidation paths

Phase 6

Add admin/moderation surfaces:

flag queue

source management

ingestion review

12. Summary

The recommended repository structure is a monorepo with three main apps:

web

api

worker

plus supporting folders for:

shared packages

documentation

scripts

infrastructure

CI/CD

This structure is strong because it mirrors the actual system architecture without overengineering it.

The key idea is simple:

deployable runtime code lives in apps/

reusable shared code lives in packages/

decision-making and architecture live in docs/

operational glue lives in scripts/ and infra/

That gives the project a clean foundation for real production work instead of an ad hoc pile of files.
