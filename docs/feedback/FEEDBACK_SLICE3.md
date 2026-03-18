# Slice 3 Creation Feedback

1. reusing slice 2 serializers (point 13) is the right call. 

2. synchronous aggregate updates on comment creation (point 12) is the correct pragmatic choice for v1
    - deferring comment_count to a background worker introduces a window where post detail reads return stale counts — bad UX for a community feed product where count feedback is part of the interaction loop.

3. conservative duplicate detection (point 7) is appropriately scoped. returning `existing_post_id` and `existing_post_slug` in the 409 response is good - it gives the client enough to redirect the user to the existing post rather than just showing an error. 

4. max depth at 6 (point 11) is a reasonable default. worth noting in the plan that this should live as a named constant, not a magic number scattered across the depth-checj logic. 


## Things that need tightening

1. `status = active` on creation has no moderation escape hatch and the plan doesn't acknowledge this. 

    - point 4 says new posts are created as active with no holding state in this slice. That’s a deliberate call, but it means from the moment Slice 3 ships, any authenticated user can post live content to public feeds with zero review. For a community platform in early launch, this is often fine — but the plan should explicitly acknowledge the implication so it’s a conscious product decision, not an oversight. Even one sentence: “Slice 3 assumes all verified users are trusted to post directly to active state; a moderation queue is a future slice concern.”

2. the 403 error case is underspecified for both endpoints.

    - both error sections list 403 forbidden if account state disallows posting/commenting — but what account states actually trigger a 403? If the answer is “none in Slice 3 because pending users never reach here,” then this error case shouldn’t be listed at all, or it should be listed as a stub placeholder. As written, it implies there’s account state logic that doesn’t exist yet. A future developer reading this might spend time looking for the account-state check. Either implement it (suspended, banned) or explicitly defer it with a note.

3. slug generation spec is incomplete for edge cases.

    - point 5 says the slug should be lowercase, URL-safe, and based on title — but doesn’t specify what happens with:
        - all-unicode/non-ASCII titles (common on an Africa-focused platform with French, Swahili, Amharic, etc.)
        - extremely long titles (what’s the max slug length?)
        - itles that produce an empty slug after normalization (e.g. a title that’s purely emoji or punctuation)
- at minimum, define a max slug length (64 or 100 chars is common) and a fallback for empty/degenerate slugs (e.g. fall back to a short random string or post-{id}). the “stable for the submitted title” requirement also means the slug helper must be pure/deterministic — worth stating explicitly.


4. domain creation is not transactionally scoped

    - point 8 says “look up an existing domain row, create one if absent.” This is a classic race condition: two concurrent link post submissions with the same hostname will both hit the lookup, find nothing, and both attempt to insert, with one failing on a unique constraint. The plan should specify: use INSERT ... ON CONFLICT DO NOTHING RETURNING * (or equivalent upsert) for domain resolution rather than a naïve check-then-insert pattern.


5. `comment_count` synchronous increment needs a locking note

    - point 12 says comment_count += 1 synchronously. in a concurrent write scenario, UPDATE posts SET comment_count = comment_count + 1 is safe at the SQL level because it’s an atomic increment — but the plan should explicitly call this out. If whoever implements this does a read-modify-write in Python (post.comment_count = post.comment_count + 1 via ORM), we will end up having a race condition under any concurrent comment load. we need to name the safe pattern in the plan.


6. POST /posts response for a link post with a newly created domain - is the domain object in the response?

    - slice 2’s post detail shape includes optional domain summary (id, hostname, display_name). The plan says creation responses reuse Slice 2 serializers, so a link post creation response should include the domain fields. But this means the service must return the resolved domain object after insert, not just the post row. The service responsibility checklist in step 7 says “return the same post-read shape” — make sure that shape includes the domain join, and that the service layer fetches or carries the domain object after resolving it in step 4.


## Minor Points

- test coverage gap: There’s no test case for a job post with body_markdown only (no URL). Point 3 says jobs accept either — that second path should have an explicit test.
- URL normalization and duplicate check ordering: The service steps list URL normalization (step 3) before duplicate check (step 5), which is correct — duplicates should always be checked against url_normalized, not raw input. Worth adding a one-line note that the 409 check uses the normalized form, not the submitted URL, so the behavior is clear.
- submitted_at vs. created_at consistency note from Slice 2: Worth carrying this forward — post creation should explicitly set submitted_at from the application write path as locked in Point 4. Make sure the service step for post insert names this field explicitly rather than leaving it to a DB default.
- build order is correct. Schemas first, then helpers, then service, then routes is the right sequence. One small addition: domain resolution helper should be built before the post-creation service, not discovered mid-implementation.