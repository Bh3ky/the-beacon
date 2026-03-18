## FEEDBACK ON SLICE 4 REVIEW


1. vote transition table (Point 4) is the standout section of the plan.
    - explicitly enumerating all six transitions before code starts eliminates the most common voting implementation bugs — ambiguous idempotency, wrong aggregate delta on vote replacement, and undefined behavior on deleting a non-existent vote. most engineers wing this and discover edge cases in production.

2. including `DELETE` routes in the same slice is the right call. 
    - a vote contract without removal is genuinely incomplete — the `viewer_vote` field in Slice 2 read responses implies the vote state can be read back, so clients will reasonably expect to be able to undo it. Deferring removal would require a follow-up slice to fix a half-shipped feature.

3. SQL-safe atomic updates locked explicitly (Point 5) is important given the Slice 3 note about `comment_count`.
    - naming the anti-pattern (Python read-modify-write) and requiring SQL-side atomics is the right constraint to put in the plan.

4. deferring self-vote restriction (Point 9) is a clean product decision, clearly reasoned.
    - the important thing is it’s an explicit decision rather than an accidental omission.

5. minimal vote response shape (Point 10) is correct.
    - returning the full post serializer on every vote would be wasteful, and it creates a coupling between the voting path and the full post read path. The minimal payload is sufficient for any client to update its local state.


## Things That Need Tightening

1. rank_score synchronous update in Slice 4 may conflict with the background worker from Slice 2.

- the Slice 2 plan established that rank_score is recalculated every five minutes via background worker cached in Redis. Point 6 now proposes updating rank_score synchronously inside every vote write transaction. These two writers will conflict — the worker will overwrite the synchronous update within minutes, but during the window between worker runs, the synchronous value will exist in the DB. Worse, if the worker formula and the synchronous helper formula ever diverge (easy to happen during iteration), you’ll have inconsistent rank_score values depending on whether the worker has run recently.

Recommendation: Pick one owner for rank_score. The cleaner v1 approach is to update upvote_count, downvote_count, and score synchronously in Slice 4, and let the background worker own rank_score exclusively. The slight staleness on rank_score is acceptable because rank position is already a background-computed property. Document this ownership split explicitly. If the worker runs every five minutes, rank order is fresh enough for an early-stage platform.

2. aggregate delta logic on vote replacement is not specified.

- Point 4 says “replace vote value and update aggregates accordingly” for a vote change — but the exact delta isn’t stated. When a user flips from +1 to -1:
	∙	upvote_count should decrease by 1
	∙	downvote_count should increase by 1
	∙	score changes by -2
- this is a three-field atomic update with specific delta values, not just an increment. The service step “update post aggregates atomically” (step 5) is too vague for this case. The plan should specify that vote replacement computes a delta from (old_value, new_value) and applies it in a single SQL update. The implementation detail matters here because getting the delta wrong produces permanently corrupted aggregate counts.

3. the rank-score helper is described as shared between post and comment paths — but post and comment rank semantics may differ.
- post rank_score uses the gravity formula ((points - 1) / (hours + 2)^1.8) established in the Beacon architecture. Comment rank ordering in Slice 2 used rank_score desc as well, but the ranking formula for comments was never locked. Comments typically don’t age the same way posts do — an old comment on a fresh post shouldn’t be penalized by age. If the shared helper applies the same gravity formula to both, comment ranking will behave oddly. The plan should either lock comment rank formula explicitly or note that comment rank_score in Slice 4 is score only (no time decay) until a comment ranking formula is defined.

4. transaction boundary for vote + aggregate update is not stated.

- the service steps list vote row write (step 4) and aggregate update (step 5) as sequential steps, but it’s not stated whether they happen in the same database transaction. They must. If the vote row is committed and the aggregate update fails, your counts are permanently wrong with no recovery path short of a full recalculation. The plan should state explicitly: vote row mutation and aggregate updates are a single atomic transaction.

5. the idempotency behavior for same-value re-vote needs to be more precise.
- point 4 says “idempotent no-op or same final state” for posting the same vote twice. These are two different behaviors from a response standpoint — a true no-op might skip the DB write entirely, while “same final state” might still write and return fresh data. For the test “posting the same vote twice is idempotent in final state,” what exactly should the second response return? Specify that the response is identical to the first — same counts, same viewer_vote — and that no aggregate mutation occurs on the second call. This prevents an implementer from accidentally double-incrementing on a retry.

Minor Points
	∙	Test gap — vote replacement for comments: The comment test suite includes upvote, vote change, delete, 401, 403, 422, and 404 — but there’s no explicit test for deleting a missing comment vote (the mirror of the post case). Add it for symmetry.
	∙	403 vote_not_allowed in error behavior: This error code is listed as a future placeholder for self-vote restriction. That’s fine, but it will confuse a developer reading the error table who’s trying to understand the current 403 surface. Add a note next to it: “not implemented in this slice — reserved for future self-vote policy.”
	∙	Account state enforcement and Slice 3 alignment (Point 8): This is now the second slice to enumerate suspended/banned as 403 triggers. Since Slice 3’s plan noted this was underspecified, it’s worth confirming that the account state check is now implemented as a shared dependency/guard rather than duplicated logic in every service. The plan should name whether this is a FastAPI Depends() guard or a shared service utility — otherwise it gets copy-pasted into each service independently.
	∙	Build order: Step 1 says vote response schemas first, which is correct. One addition: the rank-score helper (step 2) should have its formula locked in the plan before build starts, not left to the implementer — especially given the post vs. comment formula ambiguity noted above.