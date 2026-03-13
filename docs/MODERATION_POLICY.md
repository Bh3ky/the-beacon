# MODERATION_POLICY.md

## Project
**Working name:** RiftHub  
**System type:** Community-ranked discussion and discovery platform for African tech

---

# 1. Purpose

This document defines the moderation rules, responsibilities, and enforcement mechanisms for the platform.

Moderation exists to ensure that the platform remains:

- high signal
- respectful
- constructive
- trustworthy

The platform is designed to surface meaningful discussion about the African tech ecosystem. Without moderation, most discussion platforms degrade into spam, hostility, and noise.

The goal of moderation is **not control** — it is **signal preservation**.

---

# 2. Moderation Philosophy

The platform follows several guiding principles.

## 2.1 Signal over volume

More content does not equal better content.

Moderation should prioritize:

- relevance
- thoughtful discussion
- meaningful ecosystem insights

Low-effort or irrelevant posts should not dominate the platform.

---

## 2.2 Minimal but firm intervention

Moderation should not be heavy-handed.

However, when rules are violated, enforcement should be:

- consistent
- predictable
- decisive

---

## 2.3 Transparent rules

Users should clearly understand:

- what is allowed
- what is discouraged
- what is prohibited

Opaque moderation policies destroy community trust.

---

## 2.4 Human judgment matters

Moderation cannot be purely automated.

While automated detection can assist with:

- spam
- duplicate submissions
- obvious abuse

Final decisions should remain human.

---

# 3. Scope of Moderation

Moderation applies to all user-generated content.

This includes:

- posts
- comments
- usernames
- profile bios
- external links
- job postings

Moderation may also apply to:

- ingested content
- source trust levels
- domain blocking

---

# 4. Content Rules

The platform supports discussion about:

- African startups
- venture capital
- founders
- product launches
- engineering work
- policy affecting tech
- ecosystem development
- research and innovation

Content should be relevant to the African tech ecosystem.

---

# 5. Prohibited Content

The following content is not allowed.

## 5.1 Spam

Spam includes:

- repetitive promotional content
- affiliate marketing links
- referral farming
- cryptocurrency scams
- irrelevant advertising

Examples:

- posting your startup repeatedly across multiple threads
- posting unrelated marketing links
- bot-generated comments

Spam posts should be removed immediately.

Repeated offenders may be suspended or banned.

---

## 5.2 Low-effort self promotion

Self promotion is allowed **only when it provides real value**.

Examples of acceptable promotion:

- a founder sharing a launch with meaningful context
- open source project announcements
- hiring posts with useful details

Examples of unacceptable promotion:

- "Check out my startup"
- product drops without explanation
- marketing copy pasted from landing pages

Low-effort promotional content should be removed.

---

## 5.3 Harassment and abuse

The platform does not allow:

- personal attacks
- insults
- harassment
- targeted hostility

Examples:

- insulting other users
- attacking founders personally
- racist or discriminatory remarks

Constructive criticism is allowed.

Hostile behavior is not.

---

## 5.4 Hate speech

Content that targets individuals or groups based on identity is strictly prohibited.

This includes attacks based on:

- race
- ethnicity
- nationality
- religion
- gender
- sexual orientation

Such content should be removed immediately and may result in account bans.

---

## 5.5 Illegal content

Content promoting illegal activity is prohibited.

Examples:

- fraud
- hacking services
- illegal financial schemes

Posts linking to illegal activities should be removed.

---

## 5.6 Misinformation

Deliberate misinformation about companies, funding, or individuals may be moderated.

Moderators may:

- request sources
- remove misleading posts
- lock discussions spreading false information

---

## 5.7 Personal data exposure

Publishing personal information without consent is prohibited.

Examples:

- private phone numbers
- personal email addresses
- home addresses

Such content must be removed immediately.

---

# 6. Discouraged Content

The following content is discouraged but may not require removal.

## 6.1 Off-topic discussion

Posts unrelated to African tech may be removed or redirected.

Examples:

- unrelated politics
- global tech gossip without African relevance

---

## 6.2 Low quality comments

Examples:

- "first"
- "lol"
- one-word replies

These may be collapsed or removed.

---

## 6.3 Duplicate posts

If the same story is posted multiple times:

- moderators should keep the earliest submission
- duplicates should be removed

The duplicate detection system should handle most cases automatically.

---

# 7. Moderator Powers

Moderators have the authority to perform the following actions.

## 7.1 Hide content

Hidden content is not visible to normal users but remains in the database.

Used when:

- content requires review
- discussion is derailing

---

## 7.2 Remove content

Removed content is permanently hidden from public feeds.

Used for:

- spam
- abuse
- rule violations

---

## 7.3 Lock threads

Locking prevents new comments on a post.

Used when:

- discussions become hostile
- threads derail into arguments

---

## 7.4 Reclassify posts

Moderators may change the category of a post.

Example:

category: ecosystem → category: funding


---

## 7.5 Suspend users

Suspension temporarily prevents users from posting or commenting.

Used for:

- repeated rule violations
- spam activity

Suspensions may last:

- 24 hours
- 7 days
- 30 days

---

## 7.6 Ban users

Bans permanently remove access to the platform.

Used for:

- severe abuse
- repeated spam
- harassment

Banned users cannot create new accounts.

---

# 8. Flagging System

Users can flag content for moderator review.

---

## 8.1 Flag reasons

Available v1 flag reasons are:

- spam
- abuse
- misinformation
- off_topic
- other

For edge cases such as low-quality or loosely off-topic content, moderators may still act based on policy judgment, but user-submitted `reason_code` values should stay within the enum-backed set above.

---

## 8.2 Flag workflow

```text
user flags content
↓
flag stored in database
↓
moderators review queue
↓
decision made
```

---

## 8.3 Flag outcomes

Moderators may:

- dismiss the flag
- hide the content
- remove the content
- communicate a warning to the user
- suspend the user

---

# 9. Moderator Conduct

Moderators must follow certain standards.

## 9.1 Neutrality

Moderators should avoid moderating discussions where they are personally involved.

---

## 9.2 Consistency

Rules must be applied consistently.

Users should not be treated differently based on:

- popularity
- influence
- company affiliation

---

## 9.3 Transparency

Moderation decisions should be explainable.

Moderators may provide brief explanations when removing content.

---

# 10. Escalation Policy

Some moderation cases may require escalation.

Examples:

- legal threats
- coordinated harassment
- large spam attacks

Escalation steps:

1. flag internally
2. review with senior moderators
3. take platform-level action

---

# 11. Automated Moderation

Automation assists moderators but does not replace them.

Automated systems may detect:

- duplicate submissions
- spam patterns
- excessive posting
- suspicious accounts

Automated actions may include:

- temporary rate limiting
- temporary hiding of suspicious posts

Human review should follow.

---

# 12. Domain Moderation

Moderators may restrict problematic domains.

Possible actions:

| Action | Meaning |
| --- | --- |
| trust downgrade | reduces ranking influence |
| moderation review | requires approval before publishing |
| domain block | domain cannot be posted |

---

# 13. Ingestion Moderation

Ingested content must also be moderated.

Moderators may:

- reject ingestion items
- change categories
- pause or disable sources
- downgrade trust scores

---

# 14. Appeals

Users may appeal moderation decisions.

Appeals should be handled by moderators not involved in the original action.

Possible outcomes:

- decision upheld
- decision reversed
- suspension reduced

---

# 15. Community Culture

The long-term health of the platform depends on culture.

The platform should encourage:

- thoughtful discussion
- constructive criticism
- ecosystem collaboration
- knowledge sharing

The goal is to build a space where:

- founders
- engineers
- investors
- operators

can learn from each other.

---

# 16. Moderator Tools

Moderators should have access to tools such as:

- moderation queue
- flag dashboard
- user history
- domain controls
- ingestion review panel

These tools help maintain platform quality efficiently.

---

# 17. Moderator Selection

Moderators should be selected based on:

- community trust
- ecosystem involvement
- good judgment

Moderators may include:

- experienced founders
- engineers
- operators
- researchers

---

# 18. Abuse Prevention

To prevent abuse of moderation powers:

- moderation actions should be logged
- actions should be reviewable
- administrators can audit moderation activity

---

# 19. Enforcement Philosophy

Moderation should prioritize:

1. warning
2. temporary restriction
3. removal
4. suspension
5. ban

Not every violation requires a ban.

However, severe violations should be addressed quickly.

---

# 20. Launch Recommendations

At launch:

- start with **2–3 trusted moderators**
- maintain a visible moderation presence
- respond quickly to spam
- communicate rules clearly

Early moderation sets the tone for the community.

---

# 21. Summary

Moderation protects the platform’s signal quality.

The system relies on:

- community flagging
- moderator review
- automated assistance
- transparent enforcement

By maintaining clear rules and consistent moderation, the platform can become a trusted place for meaningful discussion about the African tech ecosystem.
