# Phase 4 Frontend Core Plan

Date: `2026-03-18`
Status: `slice 1 in progress`

## Goal

Turn the Phase 3 API into a usable product UI with a coherent visual system, real page flows, and working browser-side auth/write interactions.

This phase should produce the first frontend that feels like a product rather than a scaffold.

## Source Inputs

- [ROADMAP.md](/Users/telasi/Developer/RiftHub/docs/ROADMAP.md)
- [homepage-ui.md](/Users/telasi/Developer/RiftHub/docs/ui-inspo/homepage-ui.md)
- [comments-ui.md](/Users/telasi/Developer/RiftHub/docs/ui-inspo/comments-ui.md)
- [signup-signin.md](/Users/telasi/Developer/RiftHub/docs/ui-inspo/signup-signin.md)

## Visual Direction

The UI inspiration is strong and specific enough that we should treat it as the Phase 4 art direction, not just loose moodboarding.

### Locked Direction

- dark editorial UI, not generic SaaS chrome
- orange accent as the primary action color
- serif display typography for titles and content hierarchy
- monospace for metadata, nav, stats, and controls
- restrained grid/line texture in auth surfaces
- high-contrast content area with warm muted secondary text
- dense feed rows with clear ranking and category badges

### Brand Note

The visual examples use both `Rift` and `The Beacon`.

Recommendation:
- keep the product/app name as `RiftHub` in code/docs for now
- use the **visual language** from the examples, not the `The Beacon` name itself
- if naming changes later, treat that as a branding pass, not a Phase 4 blocker

## Current Frontend Reality

The actual web app is still the minimal Phase 1 scaffold:

- Next.js App Router
- Tailwind v4
- one placeholder homepage
- no shared design tokens
- no real routes
- no auth/browser integration

Important implication:
- do **not** plan this as a polish pass
- this is a real frontend build phase

## Technical Direction

### Framework

- keep Next.js App Router in `apps/web/app`
- use TypeScript throughout
- keep Tailwind v4 as the base styling layer

### Rendering Model

- use **server components** by default for public read surfaces
- use **client components** only where browser interactivity is required:
  - auth forms
  - vote controls
  - comment composer/reply toggles
  - submit forms

### Data Access

- frontend should call the existing Phase 3 API
- public reads can be fetched server-side
- authenticated mutations should use browser requests with cookies + CSRF handling

### Styling

- define CSS variables in `globals.css` for:
  - background
  - surface
  - border
  - text primary
  - text muted
  - accent orange
  - category badge colors
- do not rely on default system font styling
- introduce the editorial font pairing intentionally:
  - serif display for titles
  - mono for metadata and controls

### Locked Token Set

The CSS variable layer should match the mockups directly, not approximate them.

Recommended base tokens:

```css
:root {
  --color-bg: #0d0b08;
  --color-surface: #110e0b;
  --color-surface-hover: #130f0c;
  --color-border: #1e1a16;
  --color-border-strong: #2a2218;
  --color-text: #f0ebe3;
  --color-text-muted: #7a6255;
  --color-text-dim: #4d3e33;
  --color-text-faint: #2e2420;
  --color-accent: #e8521a;
  --color-accent-hover: #ff6b35;
  --color-accent-dim: #9e3a12;
  --color-nav-text-on-accent: #0d0b08;
  --color-success: #4ade80;
  --color-warning: #facc15;
  --color-error: #f87171;
  --color-info: #60a5fa;
  --color-opinion: #c084fc;
}
```

Category badge tokens should also be explicit:

```css
:root {
  --badge-funding-bg: #1a2e1a;
  --badge-funding-text: #4ade80;

  --badge-show-bg: #2e1a0a;
  --badge-show-text: #fb923c;

  --badge-ask-bg: #0a1a2e;
  --badge-ask-text: #60a5fa;

  --badge-opinion-bg: #2a1a2e;
  --badge-opinion-text: #c084fc;

  --badge-policy-bg: #2e2a0a;
  --badge-policy-text: #facc15;

  --badge-news-bg: #1a1a1a;
  --badge-news-text: #a1a1aa;

  --badge-job-bg: #2e1a1a;
  --badge-job-text: #f87171;
}
```

Comment-thread indent colors should also follow the mockup stack:

```css
:root {
  --indent-1: #e8521a;
  --indent-2: #c4782a;
  --indent-3: #8b6b3d;
  --indent-4: #5c4e3a;
  --indent-5: #3d3530;
}
```

Typography should map to:

- display/title serif: `DM Serif Display` or nearest editorial serif equivalent
- metadata/control mono: `IBM Plex Mono`

Locked type scale:

```css
:root {
  --fs-heading-hero: 38px;
  --fs-heading-form: 26px;
  --fs-heading-post: 22px;
  --fs-heading-success: 20px;
  --fs-heading-brand: 18px;

  --fs-body-feed-title: 15px;
  --fs-body-comment: 14px;
  --fs-body-input: 13px;
  --fs-body-base: 12px;

  --fs-meta: 11px;
  --fs-label: 10px;
  --fs-badge: 9px;

  --fs-stat-number: 24px;
  --fs-stat-secondary: 20px;
  --fs-brand-compact: 17px;
  --fs-logo-letter: 16px;
}
```

Important rule:

- if the eventual implementation uses `next/font`, the configured families should still visually match this pairing
- do not silently substitute default system stacks and call it done

## Route Scope For Phase 4

These should be the actual Phase 4 pages, in this order of importance:

1. `/`
- top feed

2. `/new`
- new feed

3. `/jobs`
- jobs feed

4. `/post/[id]/[slug]`
- post detail + comments

5. `/login`
- sign in

6. `/register`
- create account

7. `/verify`
- account verification landing/result page

8. `/submit`
- post submission

Deferred from core Phase 4 unless needed later:

- `/user/[username]`
- profile editing
- moderation/admin UI

## Feature Scope

### Public Read Surfaces

- feed navigation: top, new, jobs
- feed row rendering from real API data
- category badge rendering
- domain display
- vote/comment/time metadata
- pagination / cursor-driven “more” behavior
- post detail page
- flat API comment list rendered as a client-side nested tree

### Auth Surfaces

- register form
- login form
- verify-account page
- resend-verification entry point
- logout action in UI
- authenticated session awareness in header/nav

### Authenticated Write Surfaces

- submit post form
- add comment
- reply to comment
- vote on posts
- vote on comments

## Frontend Architecture Recommendations

### Suggested Folder Shape

Inside `apps/web`, build around:

```text
app/
  (public)/
  login/
  register/
  verify/
  submit/
  post/[id]/[slug]/
components/
  layout/
  feed/
  comments/
  auth/
  forms/
  ui/
lib/
  api/
  auth/
  comments/
  utils/
```

### Shared UI Primitives

Build a small internal set first:

- `SiteHeader`
- `FeedTabs`
- `FeedList`
- `FeedRow`
- `CategoryBadge`
- `VoteControl`
- `CommentTree`
- `CommentComposer`
- `AuthCard`
- `TextInput`
- `PasswordInput`
- `PrimaryButton`
- `MetaText`
- `Footer`

Do not overbuild a giant component system. Phase 4 needs product surfaces, not abstraction theater.

## API Integration Plan

### Read Endpoints To Consume

- `GET /v1/feeds/top`
- `GET /v1/feeds/new`
- `GET /v1/feeds/jobs`
- `GET /v1/posts/{post_id}`
- `GET /v1/posts/{post_id}/comments`

### Auth Endpoints To Consume

- `POST /v1/auth/register`
- `POST /v1/auth/resend-verification`
- `POST /v1/auth/verify`
- `POST /v1/auth/login`
- `POST /v1/auth/logout`
- `GET /v1/auth/me`

### Mutation Endpoints To Consume

- `POST /v1/posts`
- `POST /v1/posts/{post_id}/comments`
- `POST /v1/posts/{post_id}/vote`
- `DELETE /v1/posts/{post_id}/vote`
- `POST /v1/comments/{comment_id}/vote`
- `DELETE /v1/comments/{comment_id}/vote`

### Browser Auth Rules

- session remains cookie-based
- frontend must read the non-HttpOnly CSRF cookie and mirror it into `X-CSRF-Token`
- mutating requests must preserve credentials
- unauthenticated public pages must still work without session state

## Data/UX Mapping Decisions

### Feed Page

- render one compact editorial list, not card grids
- “more” pagination should use the backend cursor contract
- category badges should be color-coded but restrained
- jobs feed should look consistent with top/new, not like a separate app

### Post Detail Page

- hero area:
  - title
  - score
  - author
  - time
  - domain link
- composer directly under the post metadata
- comments displayed as nested tree reconstructed from:
  - `id`
  - `parent_comment_id`
  - `depth`

### Auth Pages

- split layout on desktop:
  - editorial left panel
  - form panel on right
- stacked layout on mobile
- register/login should be separate routes even if they share layout primitives

## Slice Plan

### Slice 1: Frontend Foundation

- replace placeholder home scaffold
- establish fonts, CSS variables, theme tokens, base layout, footer, header
- add shared primitives for buttons/inputs/meta text

Validation:

- app no longer looks like the Phase 1 scaffold
- typography and colors match the locked visual direction
- desktop and mobile both render coherently

Implementation status:

- editorial token layer landed in `globals.css`
- serif/mono foundation is in place via explicit CSS font stacks
- homepage/feed shell replaced the Phase 1 placeholder
- shared layout/feed primitives now exist for reuse in later slices

### Slice 2: Public Read Surfaces

- build `/`, `/new`, `/jobs`
- connect to live feed API
- add cursor-based “more”
- build post detail shell and comment rendering

Validation:

- public browsing works without auth
- feed pagination works
- comments render as nested tree from flat API data

### Slice 3: Auth Surfaces

- build `/login`, `/register`, `/verify`
- integrate register/login/verify/resend/me/logout
- implement cookie + CSRF browser helpers

Validation:

- verification-first flow works from UI
- login/logout state is reflected in nav and page actions
- resend path is usable from UI

### Slice 4: Authenticated Mutations

- build `/submit`
- comment composer / reply UI
- post/comment voting controls

Validation:

- authenticated users can submit posts, vote, and comment from the browser
- unauthenticated users get clear CTA or redirect behavior

## Testing and Review Requirements

### Manual Validation

- public feed browsing on desktop and mobile
- comment thread rendering with nesting
- login/register/verify/resend flow
- submit post flow
- post/comment voting
- logout and stale-auth behavior

### Code Review Focus

- no duplicated fetch/client wrappers
- no leaking CSRF logic into every component ad hoc
- server/client component boundary should stay intentional
- comment-tree transform should be deterministic and testable
- optimistic UI should be conservative unless fully sound

## Major Risks To Avoid

- building a generic component library before product pages exist
- overusing client components for read-only pages
- baking “The Beacon” naming into code if product naming is still `RiftHub`
- shipping auth forms that ignore the existing verification-first backend contract
- inventing frontend-side API contracts that differ from the real Phase 3 API

## Recommendation

Proceed with Phase 4 using the mockups as the visual source of truth and the Phase 3 API as the interaction contract.

The right implementation order is:

1. theme + layout foundation
2. public feed/detail pages
3. auth pages
4. submit/comment/vote flows

## Next Step

Review this plan first.

Once locked, implementation should start with **Slice 1: Frontend Foundation**, not the full app at once.
