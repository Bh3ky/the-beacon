## Purpose

Define the bridging strategy between verification token generation (which we have implemented in Slice 1) and a real delivery channel.

- since slice 1 currently creates verification tokens and logs them which is sufficient for development, it is not production-ready until a delivery transport is implemented.

This document proposes a clean delivery architecture that:

- keeps identity/auth logic independent from notification infrastructure
- allows development without a real email provider
- enables production email delivery without refactoring the auth domain. 

Note: this plan focuses only on verification delivery, but the architecture is intentionlly resusable for:
    - password reset
    - magic login links
    - account notifications


### Current State

**Completed (Slice 1)**

The authentication foundation already supports:

- account registration
- verification token generation
- token persistence
- token expiration policy
- verification endpoints
- session handling
- CSRF protection
- secure cookie configuration

Verification tokens are currently:

- created during registration
- stored in the database
- logged to application logs for manual testing

Example development output:

```code
INFO auth.verification
Verification token created for user_id=UUID
token=abcdef123456
```

Note: this allows manual verification testing but doesn't represent production delivery channel


### Problem

The authentication slice is architecturally complete, but not operationally complete because:

1. users cannot receive verification tokens automatically
2. production environments cannot rely on log inspection
3. token delivery logic is not abstracted

Without a delivery abstraction:

- auth services risk becoming tightly coupled to email infrastructure
- adding providers later will require refactoring


## Design Goals

The delivery solution must satisfy the following constraints.

**1. Domain isolation**

The identity/auth domain must not depend on email providers. Auth services should only emit delivery requests, not send messages directly.

**2. Environmental flexibility**

The systems must support: 

| Environment | Delivery Method        |
| --------- | ------------------------ |
| local dev   | logging or dev mailbox |
| CI tests  | no-op delivery |
| staging | real email provider |
| production | real email provider |


**3. Provider replaceability**

The system must allow replacing providers without modifying auth services.

Example future providers: Postman, Resend, Amazon SES, SendGrid, Mailgun


**4. Secure token handling**

Verification tokens must:

- never appear in API responses
- never be stored in plaintext in the database
- only appear in logs in development mode


## Proposed Architecture

The architecture introduces a delivery interface (port) with multiple implementations.

```code
Auth Service
     │
     │ create verification token
     ▼
VerificationDeliveryPort
     │
     ├── LoggingVerificationDelivery (dev)
     ├── MailpitVerificationDelivery (local mailbox)
     └── EmailVerificationDelivery (production provider)
```

Auth code only calls the delivery port. 


### Verification Flow

**Registration**

```code
POST /auth/register
```

Flow:

1. Create user (unverified)
2. Generate verification token
3. Persist token hash and expiry
4. Call verification delivery port
5. Return API response

Example flow:

```code
register()
  → create_user()
  → create_verification_token()
  → store_token_hash()
  → verification_delivery.send(user, token)
```

**Verification**

```code
POST /auth/verify
```

Flow:

1. Receive token
2. Hash token
3. Look up matching verification record
4. Validate expiration
5. Mark user as a verified
6. Invalidate token


### Delivery Interface

The delivery interface defines how verification messages are sent.

Example conceptual interface:

```code
VerificationDeliveryPort
    send_verification(user, verification_url)
```

Responsibilities:

- build verification URL
- send delivery request

Responsibilities NOT included:

- token creation
- token storage
- verification logic

Those remain inside the identity service


### Delivery Implementations

**1. Logging Delivery (current)**

Used for:
- local development
- debugging
- CI

Behavior:

```code
send_verification(user, url):
    log.info("verification_link=%s", url)
```

Advantages:
- zero dependencies
- simple debugging
- works immediately

Disadvantages:
- not usable for real users


**2. Dev Mailbox (recommended for local dev)

instead of scanning logs, we can use a local email inbox ui. recommended tool would be mailpit or mailhog style email catcher. 
    - this offers browser inbox, realistic email flow, and no real email sent among other benefits. 

Architecture:

```code
app → smtp → mailpit container → web UI
```


**3. Production Email Delivery**

- production environments should use a transactional email provider. here we will have to choose one with low to minimal operation costs.

- the delivery adapter is responsiblie for constructing email content, calling provider APIs, and handling delivery failures. 


### Verification URL Format

- verification links should follow a consistent structure. 

```code
https://app.domain.com/verify?token=<token>
```

Requirements:
- token must be URL safe
- tokens must be single use
- tokens must expire


### Token Security

- verification tokens must follow these rules:

1. Storage

Database stores 

```code
token_hash
expires_at
user_id
```

NOTE: THE PLAINTEXT TOKEN MUST NEVER BE STORED

2. Transmission

Tokens are sent only through the delivery channel.

They must never appear in:
- API responses
- logs in production


3. Expiry

Recommended default:

```code
verification_token_lifetime = 24 hours
```

Expired tokens must be rejected. 


### Configuration

Add environment-based delivery configuration.

Example:

```code
VERIFICATION_DELIVERY_MODE=log

Possible values:

| Mode | Behavior      |
| --------- | ------------------------ |
| log   | log verification URL |
| mailbox | send to local mailbox |
| email | send via provider |


### Failure Handling

Verification delivery failures should not crash registration

Recommended behavior:

```code
register()
    try send_verification()
    if failure:
        log error
        allow retry
```

An improvement to consider:

Adding endpoint:

```code
POST /auth/resend-verification


### Testing Strategy

Verification delivery must be testable.

Testing modes:

1. Unit Tests

- mock delivery interface.

Test:
- token generation
- token persistence
- delivery call triggered

2. Integration Tests

Use logging delivery mode.

Verify:
- register endpoint triggers delivery
- verification endpoint activates user

3. Manual Testing

- use dev mailbox or logs to obtain verification link


## Implementation Steps

Step 1

Introduce verification delivery interface.

⸻

Step 2

Refactor auth service to use delivery interface.

⸻

Step 3

Implement logging delivery adapter.

⸻

Step 4

Add environment configuration.

⸻

Step 5

(Optional but recommended)

Add dev mailbox support.

⸻

Step 6

Implement production email provider adapter.


## Out of Scope

This document does not cover:
- email templates
- notification systems
- password reset flows
- async job queues

These need to be added later.