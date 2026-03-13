# ROADMAP Review

## Session

- Date: 2026-03-13
- Stage: Phase 0 - Docs review
- Source reviewed this session: `docs/ROADMAP.md`

## What I changed

- cleaned up Markdown structure and syntax throughout the file
- added the missing `Phase 0` to reflect the current docs review stage
- aligned the repo structure reference to `REPO_STRUCTURE.md`
- aligned the comments API route with `API_SPEC.md`
- removed the outdated ranking formula example and replaced it with a reference to `RANKING_SYSTEM.md`
- replaced the missing `DEPLOYMENT.md` reference with `SYSTEM_ARCHITECTURE.md`
- normalized lists, code blocks, and phase validation sections

## Review Findings

### Resolved

1. The roadmap did not reflect the current working stage.
2. There were route mismatches between roadmap tasks and the API spec.
3. There was a reference to a non-existent deployment document.
4. The ranking section risked becoming a second conflicting source of truth.

### Still needing product confirmation

Resolved on 2026-03-13:

1. Moderation should be in place early so it can be tested and tuned during MVP development.
2. Jobs should be visible in the first MVP because they are an important part of the webapp.
3. Auth mode for v1 is HTTP-only cookie session with:
   - `HttpOnly`
   - `Secure`
   - `SameSite=Lax` or `SameSite=Strict` where possible
   - server-side session validation or signed session token
   - CSRF protection for state-changing requests
4. A real approved source list must be defined; placeholders are not enough.

## Implementation Notes

- `ROADMAP.md` should stay high-level and sequencing-focused.
- Detailed formulas, route contracts, and infrastructure rules should remain in their dedicated docs.
- If a roadmap section starts duplicating another doc in detail, it should usually be reduced to reference plus acceptance criteria.

## Recommendation for Next Review

The next doc worth reviewing is `docs/REPO_STRUCTURE.md` or `docs/SECURITY.md`.

Reason:

- `REPO_STRUCTURE.md` will strongly affect how Phase 1 is executed.
- `SECURITY.md` will affect architecture and API decisions before implementation starts.
