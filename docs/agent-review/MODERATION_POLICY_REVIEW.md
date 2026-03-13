# MODERATION_POLICY Review

## Session

- Date: 2026-03-13
- Stage: Phase 0 - Docs review
- Source reviewed this session: `docs/MODERATION_POLICY.md`

## Syntax cleanup completed

I made small, safe consistency fixes directly in `docs/MODERATION_POLICY.md`:

- aligned the v1 flag reasons with the enum-backed `reason_code` values already approved in schema and API docs
- converted the flag workflow into a fenced text block for cleaner rendering
- normalized the domain moderation table formatting
- clarified that source moderation can pause or disable sources
- reworded warning language so it does not imply a missing first-class moderation action type

These changes were consistency fixes, not policy rewrites.

## Findings

### 1. Flag reasons had drifted from the schema and API contract

Before this review, the policy doc listed user flag reasons such as:

- harassment
- off-topic
- low quality

But the approved schema and API contract now use the enum-backed set:

- `spam`
- `abuse`
- `misinformation`
- `off_topic`
- `other`

Impact:

- high
- inconsistent flag vocabularies create messy moderation data, harder analytics, and client-side drift

Action taken:

- updated the policy doc to use the enum-backed v1 reason codes
- added a note that edge cases such as low-quality content can still be moderated under policy judgment even if the stored `reason_code` stays within the approved set

### 2. Warning behavior exists in policy, but not yet as a first-class modeled action

The policy clearly wants moderators to be able to warn users, but the current schema action types are:

- `hide`
- `remove`
- `lock`
- `unlock`
- `restore`
- `reclassify`
- `suspend_user`
- `ban_user`
- `unsuspend_user`
- `set_domain_trust`
- `block_domain`
- `unblock_domain`
- `approve_ingestion`
- `reject_ingestion`

There is no first-class `warn_user` action at the moment.

Impact:

- medium
- if warnings matter operationally, they should be auditable and consistent rather than informal

Recommendation:

- decide whether warnings are:
  - a first-class moderation action later
  - or just moderator communication plus metadata / notes

### 3. Appeals are documented as policy, but not yet as an implementation contract

This file says:

- users may appeal moderation decisions
- appeals should be handled by moderators not involved in the original action

But there is no matching API route, schema object, or operational flow documented elsewhere yet.

Impact:

- medium
- this affects scope, admin tooling, user messaging, and audit expectations

Recommendation:

- decide whether appeals are:
  - an MVP product workflow
  - or a manual/out-of-band process at launch

### 4. The rest of the moderation direction is generally aligned

The document is otherwise in good shape:

- moderation is early and central to MVP
- domain trust and blocking fit the ranking and schema docs
- ingestion moderation aligns with source trust and review controls
- moderator actions are expected to be logged and auditable
- jobs and promotional content are treated in ways that fit the separate jobs-feed decision and signal-preservation goal

This file is materially closer to implementation than the older umbrella docs.

## Clarification answers received

Resolved on 2026-03-13:

1. Moderation appeals should remain manual/out-of-band at launch.
2. Moderator warnings should remain communication plus moderator notes only in v1.

## Recommendation for next session

Next source file in the fixed order:

- `docs/SYSTEM_ARCHITECTURE.md`

Reason:

- moderation policy is now mostly aligned with ranking, schema, and API terminology
- the next useful check is whether the infrastructure and service topology still match these accumulated product and operational decisions
