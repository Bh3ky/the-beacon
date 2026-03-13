# SECURITY.md

## Project
**Working name:** RiftHub  
**System type:** Community-ranked discovery and discussion platform for African tech

---

# 1. Purpose

This document defines the security model of the platform.

The goals of the security model are to protect:

- user accounts
- platform integrity
- ranking system reliability
- moderation authority
- infrastructure resources
- user privacy

Because this is a community platform with public submissions, security must specifically guard against:

- spam attacks
- vote manipulation
- account abuse
- malicious links
- automated bot activity
- API abuse

Security should be **built into the system from the start**, not added later.

---

# 2. Security Philosophy

The platform follows several principles.

## 2.1 Assume hostile traffic

Any public platform will eventually receive:

- spam
- scraping
- bots
- abusive users

Security must assume this is inevitable.

---

## 2.2 Defense in depth

Security should exist at multiple layers:

- frontend
- API
- database
- worker processes
- infrastructure

Failure of one layer should not compromise the entire system.

---

## 2.3 Least privilege

Services and users should only have access to the minimum privileges required.

Examples:

- moderators cannot modify database schema
- workers cannot perform moderation actions
- frontend never holds secret credentials

---

## 2.4 Auditability

All sensitive actions should be traceable.

Examples:

- moderation actions
- admin actions
- authentication events

Logs should allow operators to understand what happened and when.

---

# 3. Authentication Model

Authentication protects user accounts and platform actions.

---

# 3.1 Account Creation

Users must create accounts to:

- submit posts
- vote
- comment
- flag content

Anonymous browsing is allowed.

Required fields:

username
email
password


Optional:


display name
profile bio


---

# 3.2 Password Security

Passwords must be stored securely.

Requirements:

- hashed using bcrypt or argon2
- never stored in plaintext
- never logged

Password policies should include:

- minimum length
- basic complexity rules
- protection against extremely common passwords

---

# 3.3 Session Authentication

V1 authentication should use HTTP-only cookie sessions.

Required properties:

- `HttpOnly`
- `Secure`
- `SameSite=Lax` or `SameSite=Strict` where possible
- server-side session validation or signed session token

This reduces XSS exposure and supports server-side session invalidation.

---

# 3.4 Session Expiration

Authentication sessions should expire.

Example:


session lifetime: 7 days


Shorter expiration may be used for admin sessions.

---

# 3.5 CSRF and Origin Protection

State-changing requests must be protected with:

- CSRF validation
- request `Origin` validation

If the frontend and API are cross-origin:

- allow credentialed requests only for explicit trusted origins
- never use wildcard CORS with credentials
- keep the CSRF token out of `localStorage`

---

# 3.6 Login Protection

Protect login endpoints from abuse.

Methods:

- rate limiting
- IP throttling
- login attempt limits

Example rule:


5 failed attempts → temporary lockout


---

# 4. Authorization Model

Authorization controls what authenticated users can do.

Roles include:

| Role | Permissions |
|-----|-----|
user | vote, comment, submit |
moderator | remove content, review flags |
admin | manage sources, manage moderators |

---

# 4.1 Role Enforcement

Role checks must occur:

- server-side
- in API handlers
- before sensitive operations

Never rely solely on frontend checks.

---

# 4.2 Moderator Protection

Moderator actions must be restricted to moderator roles.

Actions include:

- removing posts
- removing comments
- suspending users
- banning users

These actions must be logged.

---

# 4.3 Admin Protection

Admin-level actions include:

- adding ingestion sources
- modifying trust scores
- managing moderators
- adjusting system configuration

Admin access should be extremely limited.

---

# 5. API Security

The API is the primary attack surface.

---

# 5.1 Rate Limiting

All critical endpoints must be rate limited.

Examples:

| Endpoint | Limit |
|---|---|
login | 5/min |
post submission | 5/hour |
comment creation | 20/min |
vote actions | 60/min |
flagging | 10/min |

Redis should be used for rate-limit counters.

---

# 5.2 Request Validation

All API requests must be validated using schema validation.

Validation includes:

- required fields
- data types
- string length limits
- URL validation

Invalid payloads should return structured errors.

---

# 5.3 Payload Size Limits

Large payloads can be abused.

Recommended limits:


post body: 20 KB
comment: 10 KB
profile bio: 2 KB


---

# 5.4 CORS Configuration

CORS should only allow trusted origins.

Example:


https://thebeacon.africa

https://staging.thebeacon.africa

http://localhost:3000


Credentialed cookie-based requests should use:

- explicit allowlisted origins only
- `allow_credentials = true`

Never allow unrestricted CORS in production.

---

# 6. Input Security

User-generated content must be treated as untrusted.

---

# 6.1 XSS Protection

User text must be sanitized before rendering.

Surfaces requiring sanitization:

- post text
- comments
- profile bios
- ingestion summaries

HTML rendering should be carefully controlled.

---

# 6.2 Markdown Safety

If markdown is supported:

- disable raw HTML
- sanitize rendered output
- restrict embedded content

---

# 6.3 URL Validation

Submitted URLs must be validated.

Checks should include:

- valid scheme (http/https)
- URL length
- domain normalization
- duplicate detection

This protects ranking integrity.

---

# 7. Spam Protection

Spam is one of the biggest threats to community platforms.

---

# 7.1 Submission Rate Limits

Limit how frequently users can submit posts.

Example:


max 5 posts per day


---

# 7.2 Comment Rate Limits

Prevent comment flooding.

Example:


max 20 comments per minute


---

# 7.3 Link Domain Monitoring

Track domains frequently posted.

Possible actions:

- downgrade domain trust
- require moderation
- block domain

---

# 7.4 Duplicate Link Detection

Prevent repeated submissions of the same article.

URL normalization should include:

- removing tracking parameters
- canonicalizing hostnames
- removing fragments

---

# 7.5 New Account Restrictions

New accounts may have limited privileges.

Example:


first 24 hours → limited submission rate


This slows automated spam campaigns.

---

# 8. Vote Manipulation Prevention

Voting determines feed ranking, so it must be protected.

---

# 8.1 One Vote per User

Users can only vote once per target.

Enforced via database constraints.

---

# 8.2 Self-Vote Prevention

Optionally prevent users from voting on their own posts.

---

# 8.3 Vote Rate Limits

Prevent automated vote manipulation.

Example:


max 60 votes per minute


---

# 8.4 Suspicious Activity Detection

Detect unusual voting patterns:

- many votes from one IP
- new accounts voting heavily
- coordinated voting

These can trigger moderation review.

---

# 9. Infrastructure Security

Infrastructure must also be secured.

---

# 9.1 Secrets Management

Secrets include:

- database credentials
- Redis credentials
- session signing or session-store secrets
- CSRF secrets
- internal tokens

Secrets must be stored in:

- Railway environment variables
- Vercel environment variables

Never commit secrets to git.

---

# 9.2 Database Access

Only API and worker services should access the database.

Frontend should never connect directly.

---

# 9.3 Redis Access

Redis should be private and authenticated.

Use:


TLS + authentication


---

# 9.4 Network Exposure

Public services:


frontend
API


Internal services:


worker
database
redis


Internal services should not expose public endpoints.

---

# 10. Logging and Monitoring

Security incidents must be observable.

---

# 10.1 Security Logs

Important events to log:

- login attempts
- failed logins
- account creation
- moderation actions
- admin actions
- suspicious vote patterns

---

# 10.2 Error Monitoring

Critical failures should trigger alerts.

Examples:

- API authentication errors
- database connection failures
- ingestion pipeline errors

---

# 10.3 Abuse Monitoring

Track indicators such as:

- spike in flags
- spike in new accounts
- unusual vote behavior

These signals may indicate coordinated abuse.

---

# 11. Data Protection

User data must be handled responsibly.

---

# 11.1 Stored User Data

Minimal user data should be stored.

Examples:


username
email
password hash
account metadata


Avoid storing unnecessary personal data.

---

# 11.2 Email Protection

Email addresses should never be publicly visible.

---

# 11.3 Data Retention

Inactive accounts and unused data may eventually be pruned.

Policies can be defined later if necessary.

---

# 12. Dependency Security

Third-party dependencies may introduce vulnerabilities.

---

# 12.1 Dependency Updates

Dependencies should be regularly updated.

Use tools such as:

- dependency scanners
- automated alerts

---

# 12.2 Package Review

Avoid unnecessary packages.

Each dependency increases the attack surface.

---

# 13. Backup Strategy

Backups protect against data loss.

---

# 13.1 Database Backups

Production database should have:

- automated backups
- restore capability

---

# 13.2 Backup Verification

Occasional restore tests should confirm backups work.

Backups that cannot be restored are useless.

---

# 14. Incident Response

When security incidents occur:

1. identify the problem
2. stop the attack
3. investigate root cause
4. patch the vulnerability
5. restore affected systems

Major incidents may require temporary feature disabling.

---

# 15. Security Checklist

Before launch, confirm:

- password hashing implemented
- auth sessions secure
- CSRF protection configured
- cross-origin cookie behavior verified
- rate limits configured
- XSS protection applied
- moderation roles enforced
- secrets not committed
- API validation working
- ingestion pipeline sanitized
- logs operational

---

# 16. Summary

Security for this platform focuses on protecting:

- community integrity
- ranking system fairness
- user accounts
- infrastructure resources

The primary threats are:

- spam
- vote manipulation
- abusive users
- automated bots

By implementing layered protections such as:

- authentication
- authorization
- rate limiting
- moderation
- monitoring

the platform can maintain a trustworthy and stable environment for discussion and di
