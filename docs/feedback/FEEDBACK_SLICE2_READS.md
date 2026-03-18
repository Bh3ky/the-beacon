## Feedback on the Phase 3 Slice 2 Reads Plan

1. flat comments with client-side tree reconstruction (point 7) is a bit pragmatic. recursive CTEs are tempting but are overkill for slice 2. perhaps `parent_comment_id + depth` is everything needs??

2. thin route handlers (point 10) agree ✅

3. opaque cursors (point 6) - base64/JSON is fine. the important thing is that the contract is opaque from day one so we can swap internals later without a client breaking change.



### what i think needs tightening

1. `top` feed cursor

- you say paginate on “a stable tuple based on ranking order” — but `rank_score` is a float and floats are terrible cursor keys. Two posts can have the same `rank_score` value, and `rank_score` changes between background worker runs, meaning a cursor encoded mid-session may produce gaps or duplicates on resume.
- the safer approach for top in v1 is to paginate on (`rank_score desc`, `id desc`) where the cursor encodes both values as a snapshot. Accept that top pagination is “best effort consistent” rather than perfectly stable. we need to lock in this explicitly so it doesn’t become a surprise bug report later.

2. viewer vote query shape needs a decision now

- point 4 says “left-joining the current user’s vote where relevant” but the bounded query note in point 5 says “a second targeted query for viewer votes if it stays bounded per page.” These are two different implementations and they have different trade-offs. Leaving both options open means whoever writes the code picks at random.
- recommendation: for feed lists, use a second targeted query (WHERE post_id = ANY(:ids) AND user_id = :viewer_id). for post detail (single row), an explicit join is fine. we need to document this split in the plan. what do you think???

3. `viewer_can_edit` window policy is underspecified

- “Author == viewer” is stated as acceptable, but there’s no mention of whether a `deleted` or `removed` post should still return `viewer_can_edit = true`. a deleted post where the author can still “edit” is a weird state. we need to add an explicit rule: `viewer_can_edit = true` only if `author == viewer` AND `post.status = active`.

4. test coverage for jobs expiry edge cases in thin

- you have “excludes expired jobs” but the jobs feed has two expiry conditions: `job_expires_at IS NULL` (no expiry) and `job_expires_at > now()`. The test suite should cover both explicitly — a job with `NULL` expiry should appear, an expired job should not, and an active job with a future expiry should appear. Three cases, one test file.

5. comment pagination 

- is it a good idea to have GET /posts/{post_id}/comments for example return 400 comments??

6. HTTP status for deleted/removed posts: The plan handles missing posts (404) but not posts that exist but are status != active (e.g. removed by a moderator). Should a removed post return 404 or 410 Gone? For a public API, 404 is safer because it doesn’t leak moderation state. Worth one sentence in the plan.

7. submitted_at vs created_at consistency: Feed ordering uses submitted_at desc but comment ordering uses created_at desc. Make sure these are genuinely different columns with different semantics in the schema, not an accidental naming inconsistency. 

Sidenote: write the Pydantic response schemas before the service layer, not after. Schemas define the contract; the service layer should be shaped to fill them, not the other way around. if we haven't already???