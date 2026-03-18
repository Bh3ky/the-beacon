# PHASE3_SLICE4_VOTING_REVIEW.md

## Purpose

Status: **implemented**

This note locked the implementation direction for **Phase 3 Slice 4: Voting** before code started and now records the decisions the implementation followed.

Slices 1 through 3 now cover auth, reads, and core content creation. Voting is the last required part of the initial Phase 3 core loop.

---

## Endpoints In Scope

Primary routes to implement:

- `POST /posts/{post_id}/vote`
- `POST /comments/{comment_id}/vote`

The API spec also defines:

- `DELETE /posts/{post_id}/vote`
- `DELETE /comments/{comment_id}/vote`

So the main question to settle before code is whether vote removal ships inside this slice or immediately after it.

My recommendation:

- implement both `POST` vote routes and both `DELETE` vote-removal routes in the same slice

Reason:

- "vote replacement/removal semantics" are already part of the locked Phase 3 plan
- leaving removal out would make the vote contract incomplete relative to `API_SPEC.md`

---

## Locked Direction

### 1. Auth and CSRF are required

All vote mutations require:

- authenticated session
- valid CSRF token
- normal origin validation from Slice 1

### 2. Route handlers stay thin

Expected ownership:

- API layer:
  - request parsing
  - dependency wiring
  - CSRF enforcement
  - response serialization
- backend/domain layer:
  - vote create/update/remove logic
  - one-vote-per-user-per-target enforcement
  - aggregate count updates
  - score updates
  - post/comment existence checks

### 3. V1 still accepts future-compatible payloads

Even if the UI exposes upvotes only, the vote service should accept:

- `1`
- `-1`

Anything else is a validation failure.

### 4. Vote transitions must be explicit

For both post votes and comment votes:

- no existing vote + `POST vote_value=1` => create vote
- no existing vote + `POST vote_value=-1` => create vote
- existing vote with same value + `POST` => idempotent no-op with the same final response payload and no aggregate mutation
- existing vote with different value + `POST` => replace vote value and update aggregates according to the explicit delta
- existing vote + `DELETE` => remove vote and update aggregates
- no existing vote + `DELETE` => return success with unchanged final state

Replacement delta must be computed from `(old_value, new_value)` and applied atomically.

Examples:

- `+1 -> -1`
  - `upvote_count - 1`
  - `downvote_count + 1`
  - `score - 2`
- `-1 -> +1`
  - `upvote_count + 1`
  - `downvote_count - 1`
  - `score + 2`

Recommended `DELETE` behavior:

- `200 OK`
- resource payload with `viewer_vote = null`

This stays aligned with the current spec and keeps clients simple.

### 5. Aggregate updates must be SQL-safe

For both posts and comments, aggregate updates must not use Python read-modify-write logic.

Use SQL-side atomic update patterns for:

- `upvote_count`
- `downvote_count`
- `score`

### 6. Score updates are synchronous in Phase 3

Phase 3 should update vote aggregates and simple score state inside the same write transaction.

For now:

- `score = upvote_count - downvote_count`

`rank_score` ownership needs to stay unambiguous.

Locked temporary Phase 3 rule:

- vote writes update aggregate counts and `score` synchronously
- `posts.rank_score` may be refreshed synchronously as a temporary write-path owner until the dedicated ranking refresh path becomes the sole owner
- `comments.rank_score` should use `score` directly for Slice 4 instead of inventing a separate decay formula

Do not let two independent implementations silently own the same `rank_score` field long-term.

### 7. Vote targets must be active resources

Voting should only be allowed on active resources.

Rules:

- missing post/comment => `404`
- non-active post/comment => `404`

Publicly removed or hidden resources should not surface different vote semantics.

### 8. Account-state enforcement should match Slice 3

Authenticated users with these states should receive `403 forbidden`:

- `suspended`
- `banned`

Pending users should not reach vote routes because they do not receive sessions.

This check should live in a shared service-layer helper, not be reimplemented separately in each route.

### 9. Self-vote restriction is not enabled unless we explicitly choose it now

The docs mention self-vote restriction as optional.

Current recommendation:

- do **not** enforce self-vote restriction in Phase 3 unless we deliberately revise the docs first

Reason:

- it is not locked elsewhere yet
- it would be easy to add later
- it is not necessary to complete the MVP loop

### 10. Response shape should stay minimal and spec-aligned

Vote mutation responses should return only the updated resource voting fields.

For posts:

- `id`
- `upvote_count`
- `downvote_count`
- `score`
- `rank_score`
- `viewer_vote`

For comments:

- `id`
- `upvote_count`
- `downvote_count`
- `score`
- `rank_score`
- `viewer_vote`

Do not return the full post/comment serializer for vote mutations.

---

## Error Behavior

Expected failures:

- `401 unauthenticated`
- `403 forbidden` for suspended/banned users
- `403 vote_not_allowed` is reserved for a future explicit policy such as self-vote restriction; it is not implemented in this slice
- `404 post_not_found`
- `404 comment_not_found`
- `422 validation_error` for invalid `vote_value`

---

## Implementation Notes

### Post vote service responsibilities

The post-vote service should:

1. verify post exists and is active
2. enforce allowed account state
3. load existing vote for `(post_id, user_id)`
4. create/update/delete vote row as needed
5. update post aggregates atomically inside the same DB transaction
6. update post `score`
7. refresh post `rank_score` under the temporary Phase 3 ownership rule
8. return the minimal post vote payload

### Comment vote service responsibilities

The comment-vote service should:

1. verify comment exists and is active
2. enforce allowed account state
3. load existing vote for `(comment_id, user_id)`
4. create/update/delete vote row as needed
5. update comment aggregates atomically inside the same DB transaction
6. update comment `score`
7. set comment `rank_score = score`
8. return the minimal comment vote payload

### Rank-score helper

Slice 4 should introduce a small helper for recomputing post rank values after vote changes.

It should be:

- deterministic
- easy to replace later when the fuller ranking module lands

Do not force comments through the same helper unless a comment-specific ranking formula is explicitly defined.

---

## Test Expectations

Minimum tests for this slice:

- authenticated post upvote creates a vote and returns updated payload
- authenticated post downvote creates a vote and returns updated payload
- posting the same vote twice is idempotent in final state
- changing vote from `1` to `-1` updates counts and score correctly
- deleting an existing post vote clears `viewer_vote`
- deleting a missing post vote still succeeds with unchanged final state
- unauthenticated post vote returns `401`
- suspended/banned user post vote returns `403`
- invalid `vote_value` returns `422`
- missing/non-active post vote target returns `404`
- authenticated comment upvote creates a vote and returns updated payload
- changing comment vote updates counts and score correctly
- deleting an existing comment vote clears `viewer_vote`
- deleting a missing comment vote still succeeds with unchanged final state
- unauthenticated comment vote returns `401`
- suspended/banned user comment vote returns `403`
- invalid `vote_value` on comment returns `422`
- missing/non-active comment vote target returns `404`

---

## Recommended Build Order

1. vote response schemas
2. rank-score recompute helper for synchronous vote writes
3. backend post-vote service
4. backend comment-vote service
5. POST vote routes
6. DELETE vote routes
7. focused Slice 4 tests
