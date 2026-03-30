# Phase 7 Moderation Plan

Date: `2026-03-24`
Status: `review-ready`

## Goal

Ship the first real moderation slice for MVP:

- moderator-only review flows
- auditable moderation actions
- a minimal flag queue UI
- enforcement that normal users cannot trigger moderator operations

Phase 7 should finish the moderation path that the schema and policy already imply. It should not try to build a full trust-and-safety platform in one pass.

## Source Inputs

- [ROADMAP.md](/Users/telasi/Developer/RiftHub/docs/ROADMAP.md)
- [MODERATION_POLICY.md](/Users/telasi/Developer/RiftHub/docs/MODERATION_POLICY.md)
- [SYSTEM_ARCHITECTURE.md](/Users/telasi/Developer/RiftHub/docs/SYSTEM_ARCHITECTURE.md)
- [ARCHITECTURE.md](/Users/telasi/Developer/RiftHub/docs/ARCHITECTURE.md)
- [REPO_STRUCTURE.md](/Users/telasi/Developer/RiftHub/docs/REPO_STRUCTURE.md)
- [MEMORY.md](/Users/telasi/Developer/RiftHub/docs/agent-review/MEMORY.md)
- [PHASE6_WORKER_PLAN.md](/Users/telasi/Developer/RiftHub/docs/agent-review/PHASE6_WORKER_PLAN.md)

External references used to shape the plan:

- OWASP Authorization Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- OWASP Logging Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
- FastAPI `Security()` / dependency authz reference: https://fastapi.tiangolo.com/reference/dependencies/
- FastAPI OAuth2 scopes reference: https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/

## Current Code Reality

Already implemented:

- `flags` table exists with open/reviewed state fields and duplicate-open-flag protection in [flag.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/models/flag.py)
- `moderation_actions` audit table exists in [moderation.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/models/moderation.py)
- moderation-related enums already exist in [types.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/db/types.py)
- user flag submission already works through [`POST /v1/flags`](/Users/telasi/Developer/RiftHub/apps/api/src/rifthub_api/routes/flags.py)
- backend flag creation rules already exist in [flags.py](/Users/telasi/Developer/RiftHub/packages/backend/src/rifthub_backend/flags.py)
- comment report UI already exists in [comment-thread.tsx](/Users/telasi/Developer/RiftHub/apps/web/components/post/comment-thread.tsx)
- API coverage exists for flag creation in [test_flags.py](/Users/telasi/Developer/RiftHub/apps/api/tests/test_flags.py)

Not implemented yet:

- moderator queue read endpoints
- moderator action endpoints
- explicit moderator/admin authz dependencies for those endpoints
- atomic moderation services that both enforce status changes and append audit rows
- post report UI parity with comment report UI
- moderation dashboard pages in the web app
- moderator review transitions for flags such as `reviewing`, `resolved`, `dismissed`
- direct tests for moderator-only access and moderation audit trails

## Scope Decision

Phase 7 should implement the MVP moderation subset from the roadmap and policy.

In scope:

- review open flags
- dismiss a flag
- remove a post
- remove a comment
- suspend a user
- ban a user
- store every moderator action in `moderation_actions`
- update related flag review state when an action resolves a flag

Explicitly out of scope for this slice:

- full warnings / moderator messaging
- bulk actions
- appeal flows
- moderator notes timeline UI
- domain/source/ingestion moderation actions beyond audit visibility
- automated moderation heuristics
- advanced queue assignment / claiming

## Target Behavior

### Roles

- `moderator` and `admin` can access moderation queue endpoints
- only `admin` should be allowed to perform the highest-risk account actions if we decide to split powers
- normal authenticated users must never reach moderation execution paths

Recommended MVP permission split:

- `moderator`: review flags, dismiss flags, remove posts/comments, suspend users
- `admin`: everything above plus ban users

This keeps the first role model simple while avoiding permanent-account actions being broadly delegated too early.

### Flag workflow

Desired flow:

```text
user submits flag
→ flag stored as open
→ moderator views open queue
→ moderator either dismisses or takes action
→ flag becomes dismissed or resolved
→ reviewed_by_user_id and reviewed_at are recorded
→ moderation_actions audit row is written when an enforcement action occurs
```

### Enforcement behavior

MVP enforcement mapping:

- remove post:
  - set post status to removed
  - hide from normal read surfaces
  - preserve row for audit/history
- remove comment:
  - set comment status to removed
  - preserve tree integrity in reads
- suspend user:
  - set user status to suspended
  - existing auth/write restrictions should continue blocking posting, commenting, and voting
- ban user:
  - set user status to banned
  - existing auth restrictions should continue to deny access

Do not hard-delete moderated content in Phase 7.

## Backend Plan

### Slice 1: moderator authz dependency

Add explicit API dependencies for moderation access rather than open-coding role checks in each route.

Target shape:

- `RequireModeratorSession`
- optional `RequireAdminSession` if ban remains admin-only

Design notes:

- keep authz centralized and testable
- use FastAPI dependency-based security composition rather than route-local branching
- return `403 forbidden` for authenticated users without moderation rights

Current status:

- implemented

### Slice 2: shared moderation service

Add a backend moderation service module responsible for:

- resolving target row
- validating the requested action against target type
- applying the status mutation
- writing the `moderation_actions` audit row
- optionally transitioning related flag rows
- committing atomically

Recommended service boundaries:

- `list_open_flags(...)`
- `dismiss_flag(...)`
- `moderate_post(...)`
- `moderate_comment(...)`
- `moderate_user(...)`

Important constraint:

- audit write and target mutation must happen in the same transaction

Current status:

- implemented for dismiss, remove, suspend, and ban flows

### Slice 3: moderation routes

Add minimal API routes such as:

- `GET /v1/moderation/flags`
- `POST /v1/moderation/flags/{flag_id}/dismiss`
- `POST /v1/moderation/posts/{post_id}/remove`
- `POST /v1/moderation/comments/{comment_id}/remove`
- `POST /v1/moderation/users/{user_id}/suspend`
- `POST /v1/moderation/users/{user_id}/ban`

API response rules:

- return enough flag and target summary data to drive the first dashboard
- do not expose reporter private notes broadly outside moderator surfaces
- keep action payloads explicit and narrow; avoid generic “run any moderation action” endpoints

Current status:

- implemented

### Slice 4: read-layer and schema adjustments

Likely additions:

- moderator queue payload models
- flag summary payloads with target summary and reporter summary
- moderation action payloads if audit history is exposed in the dashboard

Potential follow-up:

- add `viewer_can_moderate` usage in more web surfaces if moderator affordances should appear inline later

## Frontend Plan

### Slice 5: report parity and dashboard shell

Add:

- post report action matching the existing comment report flow
- `/moderation` page for moderators
- open flag queue list

Current status:

- pending
- implemented

First dashboard can stay simple:

- queue table or list
- target type
- reason
- reporter
- created time
- target preview
- action controls

### Slice 6: moderator action UI

Support:

- dismiss flag
- remove post
- remove comment
- suspend user
- ban user if admin-only path is enabled

UI rules:

- actions should require explicit confirmation for destructive account actions
- action forms should capture a short moderator reason
- optimistic UI is not necessary here; correctness matters more than speed

Current status:

- pending
- implemented

## Data and Audit Rules

Per the policy and OWASP logging guidance, moderation actions should capture at least:

- when
- who performed the action
- what target type/id was affected
- which action was taken
- result status
- moderator-supplied reason

For RiftHub, the canonical audit source should remain the `moderation_actions` table.

Recommended `metadata_json` usage in MVP:

- originating `flag_id` if action came from a queue item
- previous status
- new status
- optional duration for suspensions if temporary suspension windows are introduced in a later slice

Do not log secrets, session tokens, or raw CSRF values into moderation metadata.

## Validation Plan

Backend tests:

- moderator role can access moderation routes
- normal user gets `403`
- admin-only actions reject plain moderator if we split powers
- dismissing a flag updates review fields correctly
- moderation action writes an audit row
- target mutation and audit row are atomic
- removed posts/comments no longer appear in normal reads
- suspended/banned users are blocked by existing write/auth rules

Frontend / integration checks:

- moderator dashboard renders only for authorized accounts
- queue loads and actions update visible state
- post and comment flagging both work
- non-moderators cannot see moderation controls

Manual review focus:

- removed comment rendering still preserves thread readability
- removed post behavior is consistent between feeds and direct detail pages
- moderator flow does not leak unnecessary reporter data into normal user views

## Exit Criteria

Phase 7 is complete enough when all of the following are true:

- users can flag posts and comments through the public UI
- moderators can review open flags in a dedicated dashboard
- moderators can dismiss flags and execute the MVP enforcement actions
- every enforcement action creates a durable audit row
- moderation routes are protected by explicit role checks
- normal users cannot trigger moderation actions
- automated and manual tests cover the permission and audit trail paths

## Recommended Build Order

1. Moderator/admin API authz dependencies
2. Shared moderation service with audit writes
3. Moderator routes for queue and actions
4. Post reporting UI parity
5. Minimal moderation dashboard
6. Validation and hardening pass

## Recommendation

Treat Phase 7 like the earlier hardening phases:

- do not build a generic moderation engine first
- implement the narrow roadmap actions explicitly
- keep moderation decisions human and auditable
- preserve deleted/removed content rows for history instead of hard deletion

This should give RiftHub enough moderation capability to operate the MVP safely without prematurely building a complex trust-and-safety subsystem.
