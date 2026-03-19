# Phase 4 Dev Feed Seed Note

Date: `2026-03-19`

## Goal

Populate the local feed with richer homepage data without reintroducing frontend hardcoded rows.

## Decision

- The frontend continues to render real backend data only.
- Rich sample homepage content is provided through a development seed fixture instead of UI literals.
- The fixture lives at:
  - [dev_feed_posts.json](/Users/telasi/Developer/RiftHub/scripts/seed-data/dev_feed_posts.json)
- The seed command is:
  - `npm run db:seed:feed`

## Notes

- The fixture uses the mockup titles/authors/domains/points/comment counts as inspiration.
- Category values are constrained by the real backend enum, so some “news-like” examples map to existing backend categories such as `ecosystem` or `engineering`.
- The seed script is intended for local development only.
- The script refreshes seed-owned comments on the seeded posts so feed metadata stays coherent.
