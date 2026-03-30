# Operations Roles Setup

Date: `2026-03-24`
Status: `current implementation`

## Purpose

This document explains how to set up the first internal operator accounts for RiftHub.

Use it when you need to create:

- initial admin accounts
- initial moderator accounts

This is intentionally a local/operator workflow.
There is no public role-management API in the product.

## Current Role Model

Supported user roles:

- `user`
- `moderator`
- `admin`

Current moderation/ingestion access model:

- moderators and admins can view `/moderation`
- moderators and admins can review community flags
- moderators and admins can view ingestion queue and source health
- only admins can approve or reject ingestion items
- only admins can ban users

## Important Constraint

Do not try to create admins directly through the public registration flow.

The correct process is:

1. register normal accounts
2. verify those accounts
3. promote them locally with the role bootstrap command

That keeps privileged role assignment out of the public API surface.

## Prerequisites

From the repo root:

```bash
npm install
uv sync --all-packages
cp .env.example .env
```

Then make sure your local services are up:

```bash
npm run db:up
npm run api:dev
npm run web:dev
```

## Step 1: Create The Accounts

Register the accounts normally through the app UI or the auth API.

Recommended internal identities:

- `admin1`
- `admin2`
- `moderator1`

At this stage they will still be normal users in pending/verification flow.

## Step 2: Verify The Accounts

Each account must complete the normal verification flow first.

In local development, verification tokens come from the configured local delivery path:

- `log`
- or `mailpit`

Once verified, the accounts become active.

Do not promote accounts that are still pending if you want a clean operational setup.

## Step 3: Assign Roles

Use the local bootstrap command from the repo root:

```bash
npm run db:set-role -- --email admin1@example.com --role admin
npm run db:set-role -- --email admin2@example.com --role admin
npm run db:set-role -- --email moderator1@example.com --role moderator
```

Accepted role values:

- `user`
- `moderator`
- `admin`

The command updates an existing user by email.

If successful, it prints:

```text
[ok] admin1@example.com -> role=admin
```

If the user does not exist, it fails cleanly.

## Recommended First In-House Setup

For your immediate setup:

```bash
npm run db:set-role -- --email <first-admin-email> --role admin
npm run db:set-role -- --email <second-admin-email> --role admin
npm run db:set-role -- --email <moderator-email> --role moderator
```

## Verification Checks

After role assignment, verify:

- both admin accounts can access `/moderation`
- the moderator account can access `/moderation`
- the moderator can view ingestion review items but cannot approve/reject them
- admins can approve/reject ingestion items
- only admins can ban users

## Safety Notes

- treat the role bootstrap command as an operator-only local tool
- do not expose it through the public frontend or API
- keep the number of admin accounts small
- prefer two admins for recovery/continuity, not many
- use moderator accounts for routine queue review where full admin power is not required

## Current Limitation

There is still no dedicated admin UI for changing roles.
Today, role assignment is deliberately a local script workflow.
