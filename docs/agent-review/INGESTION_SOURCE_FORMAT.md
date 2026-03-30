# Ingestion Source Format

Date: `2026-03-24`
Status: `current implementation`

## Purpose

This is the operator-facing reference for the ingestion system as it exists today.

Use this document when:

- preparing the real approved source list
- validating whether a source can be ingested by the current worker
- checking which fields in the seed JSON are actually used

## Runtime Support

The current ingestion runtime supports:

- `rss` source polling
- RSS/Atom feed parsing through `feedparser`
- JSON seed-file import for approved sources

The schema also allows these source types:

- `api`
- `manual`
- `scraper`

But those are not implemented as active ingestion runtimes yet. They can be stored in the database, but the current worker will not poll them.

## Seed File Format

The current source seed file is a JSON document with a top-level `sources` array.

Example shape:

```json
{
  "version": 1,
  "environment": "development",
  "description": "Approved sources",
  "sources": [
    {
      "name": "TechCabal",
      "source_type": "rss",
      "status": "active",
      "feed_url": "https://techcabal.com/feed/",
      "base_url": "https://techcabal.com",
      "categories": ["news", "funding"],
      "trust_score": 0.85,
      "auto_publish": false,
      "poll_interval_minutes": 30
    }
  ]
}
```

## Required Source Fields

Each source entry must provide:

- `name`
- `source_type`
- `status`
- one usable source URL field:
  - `feed_url`
  - `api_endpoint`
  - `entry_url`
  - `url`

If none of those URL fields is present, the import fails.

## Source Fields Currently Used

These fields are actively consumed by the importer today:

- `name`
- `source_type`
- `status`
- `feed_url` or `api_endpoint` or `entry_url` or `url`
- `site_url` or `base_url`
- `default_category`
- `categories`
- `trust_score`
- `auto_publish`
- `poll_interval_minutes`

How they map today:

- `feed_url` / `api_endpoint` / `entry_url` / `url`
  - the importer picks the first non-empty one in that order
- `site_url` / `base_url`
  - used as the source site URL if present
- `default_category`
  - preferred if valid
- `categories`
  - fallback only; the first recognized category is used if `default_category` is absent
- `trust_score`
  - must be greater than zero
- `auto_publish`
  - if `true`, normalized non-duplicate items can publish automatically
- `poll_interval_minutes`
  - must be greater than zero

## Source Fields Currently Ignored

These fields appear in the development seed file but are not used by the current importer/runtime:

- `slug`
- `review_first`
- `default_post_type`
- `language`
- `notes`
- top-level `review_first_default`

They are harmless metadata today, but they do not affect ingestion behavior.

## Allowed Enum Values

Currently accepted source enums:

- `source_type`: `rss`, `api`, `manual`, `scraper`
- `status`: `active`, `paused`, `disabled`

Current runtime behavior:

- only `active` + `rss` sources are polled
- `paused` and `disabled` sources are stored but skipped by polling

## Category Handling

Accepted categories come from the platform taxonomy:

- `funding`
- `launch`
- `policy`
- `opinion`
- `ask`
- `show`
- `jobs`
- `engineering`
- `ecosystem`

Current alias handling:

- `news` maps to `ecosystem`

If `default_category` is missing, the importer scans `categories` and uses the first recognized value.

## URL Rules

Source URLs and site URLs are normalized before storage.

Current normalization rules:

- only `http` and `https` URLs are accepted
- hostnames are lowercased
- default ports `80` and `443` are removed
- fragments are removed
- common tracking query params are stripped
- remaining query params are sorted deterministically

Examples of stripped tracking params:

- `utm_*`
- `mc_*`
- `fbclid`
- `gclid`
- `igshid`
- `mkt_tok`
- `ref`
- `ref_src`
- `source`

## Feed Entry Requirements

For a polled RSS/Atom entry to become an ingestion item, the parser currently requires:

- `title`
- `link`

Optional entry fields:

- `id`
- `published_parsed`
- `updated_parsed`

Current entry behavior:

- entries missing `title` or `link` are skipped
- entries whose URL or title cannot be normalized are skipped
- `id` becomes `external_id` when present
- `published_parsed` is preferred for external publication time
- `updated_parsed` is used if `published_parsed` is absent

## Publication Behavior

Current staged-item flow:

```text
poll rss source
→ parse entries
→ normalize URL/title/time
→ persist ingestion item
→ dedupe against active posts
→ classify category
→ if source.auto_publish then publish
→ else move to awaiting_review
```

Current publish rules:

- published ingestion items become normal `link` posts
- ingested posts are attributed to the ingestion system user
- duplicates are marked on the ingestion item and do not create a new post

## What To Put In The Real MVP Source File

For the real rollout file, prefer this minimal practical shape per entry:

- `name`
- `source_type: "rss"`
- `status: "active"`
- `feed_url`
- `base_url`
- `default_category` or at least one recognized category in `categories`
- `trust_score`
- `auto_publish`
- `poll_interval_minutes`

Recommended rollout guidance:

- use `rss` only for the first real source list
- start with `auto_publish: false` unless the source is genuinely trusted
- keep `poll_interval_minutes` conservative at first, for example `30` or `60`
- avoid placeholder metadata that implies unsupported runtime behavior

## Current Limitations

These are the important current limits to remember:

- `api`, `manual`, and `scraper` sources are stored but not executed
- source `slug` is not used as an identity key
- there is no operator UI for editing sources yet; the seed/import path is still the main setup path
- the committed dev seed file is dummy data and should not be treated as the production source list
