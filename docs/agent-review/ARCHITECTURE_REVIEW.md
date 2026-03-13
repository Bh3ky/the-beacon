# ARCHITECTURE Review

## Session

- Date: 2026-03-13
- Stage: Phase 0 - Docs review
- Source reviewed this session: `docs/ARCHITECTURE.md`

## Syntax cleanup completed

I made small, safe fixes directly in `docs/ARCHITECTURE.md`:

- corrected malformed subsection headings
- fixed obvious typos
- fixed a broken index reference for `rank_score`

These were formatting and readability fixes only, not architectural rewrites.

## Findings

### 1. Authentication model conflicts with the now-resolved project decision

`ARCHITECTURE.md` still says:

- auth module handles "session/JWT issuance"
- auth model is "secure session or JWT-based auth"

This conflicts with the resolved project decision:

- v1 auth must use HTTP-only cookie sessions
- cookies must be `HttpOnly`, `Secure`, and `SameSite=Lax` or `SameSite=Strict` where possible
- state-changing requests need CSRF protection

Impact:

- medium to high
- this will affect API design, frontend session handling, middleware, and security implementation

Recommendation:

- update `ARCHITECTURE.md` to make cookie-session auth the only v1 mode
- mention CSRF explicitly in the auth and security sections

### 2. Source model conflicts with newer ingestion and schema docs

`ARCHITECTURE.md` describes `sources` using:

- `is_active`
- `trust_level`

But the newer docs and API direction lean toward richer source metadata such as:

- `status`
- `trust_score`
- `auto_publish`
- operational timestamps and error visibility

Impact:

- high
- affects DB schema, admin APIs, worker behavior, and ingestion controls

Recommendation:

- treat `DATABASE_SCHEMA.md`, `INGESTION_PIPELINE.md`, and `API_SPEC.md` as the newer source of truth
- update `ARCHITECTURE.md` to stop describing an older, narrower `sources` shape

### 3. Moderation flags route conflicts with API spec direction

`ARCHITECTURE.md` lists:

- `GET /admin/flags`

But the dedicated API spec uses:

- `GET /moderation/flags`

Impact:

- medium
- affects frontend admin tooling, role guards, and route naming consistency

Recommendation:

- choose one route namespace and apply it across all docs
- current direction appears to favor `moderation` for flag review

Resolved later:

- canonicalized to `GET /moderation/flags`

### 4. Frontend route shape is older than the newer route pattern

`ARCHITECTURE.md` lists:

- `/post/[id]`

But newer docs use:

- `/post/{id}/{slug}` at the API/doc level
- slug-aware routing in the frontend architecture docs

Impact:

- medium
- affects SEO, canonical URLs, routing, and link generation

Recommendation:

- update this document to use slug-aware post routes if that is the intended v1 behavior

### 5. This document overlaps heavily with later specialized docs

`ARCHITECTURE.md` still contains detailed sections on:

- database schema
- ranking formulas
- API endpoint inventory
- security
- frontend architecture
- deployment topology

Those now exist in dedicated docs:

- `DATABASE_SCHEMA.md`
- `RANKING_SYSTEM.md`
- `API_SPEC.md`
- `SECURITY.md`
- `SYSTEM_ARCHITECTURE.md`

Impact:

- high over time
- this document is likely to drift and become a second source of truth

Recommendation:

- keep `ARCHITECTURE.md` as the top-level product and system overview
- reduce detailed duplicated sections to short summaries plus references

### 6. Naming is inconsistent with the rest of the docs set

This document used an older working name, while newer docs now use:

- `RiftHub`

Impact:

- low to medium
- not a blocker, but it creates naming uncertainty in planning and implementation

Recommendation:

- use one consistent naming convention across all docs

Resolved later:

- standardized the product name to `RiftHub` across the docs set

### 7. One product-model inconsistency still needs confirmation

This document treats:

- `show` as a category

Some other docs have previously implied "show" like a post type or submission mode.

Impact:

- medium
- affects forms, validation, DB enums, and feed logic

Recommendation:

- confirm whether `show` is strictly a category on top of `text` or `link`, or whether it ever behaves like its own content type

## Clarification questions

1. Should `ARCHITECTURE.md` be reduced into a top-level overview doc with references out to the specialized docs, or do you want it to remain the long "all-in-one" architecture narrative?
2. Should I treat `DATABASE_SCHEMA.md`, `API_SPEC.md`, `RANKING_SYSTEM.md`, and `SYSTEM_ARCHITECTURE.md` as the authoritative replacements whenever they conflict with `ARCHITECTURE.md`?
3. For v1, do you want the frontend route canonically documented as `/post/[id]/[slug]` everywhere?
4. Can I standardize the source model everywhere around `status`, `trust_score`, and `auto_publish`, instead of older fields like `is_active` and `trust_level`?
5. Is `show` definitively a category and not a separate post type?

## Clarification answers received

Resolved on 2026-03-13:

1. `ARCHITECTURE.md` should be reduced into a high-level overview that points to specialized docs.
2. When `ARCHITECTURE.md` conflicts with newer dedicated docs, the newer dedicated docs are authoritative.
3. The canonical frontend route for v1 is `/post/[id]/[slug]`.
4. The source model can be standardized around `status`, `trust_score`, and `auto_publish`.

Still open:

5. Whether `show` should be a post type or remain a category.

Resolved on 2026-03-13 after follow-up:

- `show` remains a category, not a post type.
- Intended meaning: a feed/category where people showcase what they built, for example open-source projects, launches, demos, and similar maker-style posts.

## Recommendation for next session

Next source file in the fixed order:

- `docs/DATABASE_SCHEMA.md`

Reason:

- several of the most important conflicts found here point directly at the schema model
- resolving schema authority early will make later API and implementation planning much cleaner
