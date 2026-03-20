from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from rifthub_backend import dispose_engine
from rifthub_backend.creation import hostname_from_url, normalize_url, slugify_title
from rifthub_backend.db.session import get_session_factory
from rifthub_backend.db.types import Category, CommentStatus, PostStatus, PostType, UserRole, UserStatus
from rifthub_backend.models.comment import Comment
from rifthub_backend.models.domain import Domain
from rifthub_backend.models.post import Post
from rifthub_backend.models.user import User
from rifthub_backend.models.vote import CommentVote, PostVote
from rifthub_backend.voting import compute_post_rank_score

FIXTURE_PATH = Path(__file__).with_name("dev_feed_posts.json")
SEED_EMAIL_DOMAIN = "seed.rifthub.dev"
COMMENT_AUTHOR_POOL = (
    "builderzw",
    "nairobidev",
    "kofi_atta",
    "fintech_ng",
    "bheki_dev",
    "talentwatch",
    "infrabuilder",
    "cairo_startup",
    "chipperhiring",
)

COMMENT_LIBRARY: dict[Category, tuple[str, ...]] = {
    Category.FUNDING: (
        "The headline is large, but the more important question is what this capital unlocks operationally over the next 18 months.",
        "Would love to know how much of this goes into expansion versus hardening the core rails they already have.",
        "This keeps reinforcing that African fintech winners are infrastructure companies first and branding stories second.",
        "The regional angle matters here. West Africa keeps producing the clearest scale cases for payment products.",
        "Curious whether the margin story improves with this scale or if the capital mostly buys network effects and trust.",
    ),
    Category.SHOW: (
        "This is the kind of build-in-public post I want more of here. Specific product, specific users, real shipping.",
        "The best part is usually the ugly implementation details. If you publish a postmortem later, people will read it.",
        "Open-sourcing this is smart. Distribution through developer trust compounds faster than launch hype.",
        "Feels useful immediately, which is rare. The next question is whether teams can adopt it without heavy support.",
        "Would be great to see benchmarks, docs quality, and examples from production usage over time.",
    ),
    Category.OPINION: (
        "This argument lands because it is grounded in customer reality rather than imported startup theatre.",
        "The local-market lens is uncomfortable for some investors, but it usually produces stronger businesses.",
        "Pieces like this are useful because they challenge the assumptions people smuggle into strategy decks.",
        "I keep coming back to how many metrics are proxies for prestige rather than product-market fit.",
        "This is the kind of essay founders should forward to their teams before annual planning.",
    ),
    Category.POLICY: (
        "The important part is not the announcement but how consistently regulators enforce the operational details.",
        "Would like to see a simpler summary of what changes for builders on Monday morning, not just legal wording.",
        "Policy clarity matters because founders can finally decide whether to invest or wait on the sidelines.",
        "The market usually reacts less to the headline and more to whether compliance costs become predictable.",
        "If this reduces ambiguity for operators, that alone is a meaningful improvement over the status quo.",
    ),
    Category.ASK: (
        "If billing reliability matters, I would optimize for support quality and local payment options before raw infra specs.",
        "We learned the hard way that uptime numbers are less useful than incident response speed for small teams.",
        "Worth splitting the problem into hosting, observability, and payments because different vendors win on different layers.",
        "If your users are in multiple regions, latency alone should not decide this. Support and invoicing matter more than people admit.",
        "I would shortlist providers that let you start small without punishing you on simple operational tasks.",
    ),
    Category.ECOSYSTEM: (
        "The ecosystem shift is interesting because it changes how companies think about senior talent and distributed teams.",
        "Stories like this usually signal a broader market realignment rather than just one company changing strategy.",
        "This is probably good for engineers who want more optionality without leaving the continent.",
        "The second-order effect is that more local companies can hire proven operators instead of only competing for juniors.",
        "Would love to see hard numbers on placement quality and retention rather than just expansion rhetoric.",
    ),
    Category.ENGINEERING: (
        "Infrastructure failures at off-peak hours usually expose the real shape of your system better than daytime traffic does.",
        "This is the sort of post that separates nice architecture diagrams from production engineering reality.",
        "Payments reliability is still a trust problem as much as a technical one. Users remember every failed midnight transfer.",
        "Would be useful to know whether the weak point is network dependencies, bank integrations, or internal retry logic.",
        "Engineering teams on the continent have learned to design for degraded conditions better than most people appreciate.",
    ),
    Category.JOBS: (
        "Good to see a role explicitly scoped for the continent instead of pretending time zones and context do not matter.",
        "The strongest job posts are the ones that describe the real operating environment, not just the toolchain.",
        "This looks interesting if the team has clear ownership boundaries and realistic on-call expectations.",
        "Remote across Africa only works well when compensation and career growth are spelled out early.",
        "I hope more companies post with this level of role specificity instead of generic 'senior engineer' templates.",
    ),
}


@dataclass(frozen=True, slots=True)
class FeedSeedFixture:
    title: str
    domain: str | None
    url: str | None
    points: int
    author: str
    hours_ago: int
    comments: int
    category: Category
    post_type: PostType
    body_markdown: str | None
    job_expires_in_days: int | None
    threaded_comments: tuple["SeedCommentFixture", ...]


@dataclass(frozen=True, slots=True)
class SeedCommentFixture:
    author: str
    body_markdown: str
    score: int
    minutes_after_post: int
    replies: tuple["SeedCommentFixture", ...]


def parse_threaded_comments(items: list[dict[str, Any]] | None) -> tuple[SeedCommentFixture, ...]:
    if not items:
        return ()

    def parse_item(item: dict[str, Any]) -> SeedCommentFixture:
        return SeedCommentFixture(
            author=item["author"],
            body_markdown=item["body_markdown"],
            score=int(item["score"]),
            minutes_after_post=int(item["minutes_after_post"]),
            replies=parse_threaded_comments(item.get("replies")),
        )

    return tuple(parse_item(item) for item in items)


def count_threaded_comments(items: tuple[SeedCommentFixture, ...]) -> int:
    return sum(1 + count_threaded_comments(item.replies) for item in items)


def load_fixture() -> list[FeedSeedFixture]:
    payload = json.loads(FIXTURE_PATH.read_text())
    return [
        FeedSeedFixture(
            title=item["title"],
            domain=item.get("domain"),
            url=item.get("url"),
            points=int(item["points"]),
            author=item["author"],
            hours_ago=int(item["hours_ago"]),
            comments=int(item["comments"]),
            category=Category(item["category"]),
            post_type=PostType(item["post_type"]),
            body_markdown=item.get("body_markdown"),
            job_expires_in_days=item.get("job_expires_in_days"),
            threaded_comments=parse_threaded_comments(item.get("threaded_comments")),
        )
        for item in payload["posts"]
    ]


async def resolve_or_create_user(*, db: AsyncSession, username: str) -> User:
    user = await db.scalar(select(User).where(User.username == username))
    if user is not None:
        return user

    now = datetime.now(UTC)
    user = User(
        username=username,
        email=f"{username}@{SEED_EMAIL_DOMAIN}",
        password_hash="seed-password-hash",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        created_at=now,
        updated_at=now,
        last_active_at=now,
    )
    db.add(user)
    await db.flush()
    return user


async def resolve_or_create_domain(*, db: AsyncSession, hostname: str) -> Domain:
    domain = await db.scalar(select(Domain).where(Domain.hostname == hostname))
    if domain is not None:
        return domain

    now = datetime.now(UTC)
    domain = Domain(
        hostname=hostname,
        display_name=hostname,
        created_at=now,
        updated_at=now,
        last_seen_at=now,
    )
    db.add(domain)
    await db.flush()
    return domain


def make_comment_body(*, fixture: FeedSeedFixture, index: int) -> str:
    library = COMMENT_LIBRARY.get(fixture.category, ())
    if not library:
        return f"Interesting thread on {fixture.title.lower()}."

    opener = library[index % len(library)]
    if fixture.post_type == PostType.TEXT and fixture.body_markdown:
        return f"{opener} The prompt is good too: {fixture.body_markdown}"
    return opener


def comment_author_for_index(*, fixture: FeedSeedFixture, index: int) -> str:
    pool = [username for username in COMMENT_AUTHOR_POOL if username != fixture.author]
    return pool[index % len(pool)]


async def seed_threaded_comment(
    *,
    db: AsyncSession,
    post: Post,
    post_submitted_at: datetime,
    fixture: SeedCommentFixture,
    parent_comment: Comment | None = None,
) -> int:
    author = await resolve_or_create_user(db=db, username=fixture.author)
    created_at = post_submitted_at + timedelta(minutes=fixture.minutes_after_post)
    comment = Comment(
        post_id=post.id,
        author_id=author.id,
        parent_comment_id=parent_comment.id if parent_comment is not None else None,
        body_markdown=fixture.body_markdown,
        status=CommentStatus.ACTIVE,
        depth=0 if parent_comment is None else parent_comment.depth + 1,
        upvote_count=fixture.score,
        downvote_count=0,
        score=fixture.score,
        rank_score=float(fixture.score),
        created_at=created_at,
        updated_at=created_at,
    )
    db.add(comment)
    await db.flush()

    count = 1
    for reply in fixture.replies:
        count += await seed_threaded_comment(
            db=db,
            post=post,
            post_submitted_at=post_submitted_at,
            fixture=reply,
            parent_comment=comment,
        )
    return count


async def seed_post(*, db: AsyncSession, fixture: FeedSeedFixture) -> None:
    author = await resolve_or_create_user(db=db, username=fixture.author)
    normalized_url: str | None = None
    domain: Domain | None = None
    if fixture.url:
        normalized_url = normalize_url(fixture.url)
        domain = await resolve_or_create_domain(db=db, hostname=hostname_from_url(normalized_url))

    post = await db.scalar(select(Post).where(Post.author_id == author.id, Post.title == fixture.title))

    comment_total = (
        count_threaded_comments(fixture.threaded_comments)
        if fixture.threaded_comments
        else fixture.comments
    )
    submitted_at = datetime.now(UTC) - timedelta(hours=fixture.hours_ago)
    last_commented_at = submitted_at + timedelta(minutes=max(comment_total, 1))
    job_expires_at = (
        datetime.now(UTC) + timedelta(days=fixture.job_expires_in_days)
        if fixture.job_expires_in_days is not None
        else None
    )

    if post is None:
        post = Post(
            author_id=author.id,
            post_type=fixture.post_type,
            category=fixture.category,
            title=fixture.title,
            slug=slugify_title(fixture.title),
            url=fixture.url,
            url_normalized=normalized_url,
            domain_id=domain.id if domain is not None else None,
            body_markdown=fixture.body_markdown,
            status=PostStatus.ACTIVE,
            upvote_count=fixture.points,
            downvote_count=0,
            comment_count=comment_total,
            score=fixture.points,
            rank_score=compute_post_rank_score(score=fixture.points, submitted_at=submitted_at),
            submitted_at=submitted_at,
            last_commented_at=last_commented_at if comment_total > 0 else None,
            job_expires_at=job_expires_at,
            created_at=submitted_at,
            updated_at=submitted_at,
        )
        db.add(post)
        await db.flush()
    else:
        post.post_type = fixture.post_type
        post.category = fixture.category
        post.slug = slugify_title(fixture.title)
        post.url = fixture.url
        post.url_normalized = normalized_url
        post.domain_id = domain.id if domain is not None else None
        post.body_markdown = fixture.body_markdown
        post.status = PostStatus.ACTIVE
        post.upvote_count = fixture.points
        post.downvote_count = 0
        post.comment_count = comment_total
        post.score = fixture.points
        post.rank_score = compute_post_rank_score(score=fixture.points, submitted_at=submitted_at)
        post.submitted_at = submitted_at
        post.last_commented_at = last_commented_at if comment_total > 0 else None
        post.job_expires_at = job_expires_at
        post.updated_at = submitted_at

    await db.execute(delete(PostVote).where(PostVote.post_id == post.id))
    await db.execute(
        delete(CommentVote).where(
            CommentVote.comment_id.in_(select(Comment.id).where(Comment.post_id == post.id))
        )
    )
    await db.execute(delete(Comment).where(Comment.post_id == post.id))
    await db.flush()

    if fixture.threaded_comments:
        for threaded_comment in fixture.threaded_comments:
            await seed_threaded_comment(
                db=db,
                post=post,
                post_submitted_at=submitted_at,
                fixture=threaded_comment,
            )
    else:
        for index in range(fixture.comments):
            comment_created_at = submitted_at + timedelta(minutes=index + 1)
            comment_score = max(1, min(12, fixture.points // max(index + 4, 4)))
            comment_author = await resolve_or_create_user(
                db=db,
                username=comment_author_for_index(fixture=fixture, index=index),
            )
            db.add(
                Comment(
                    post_id=post.id,
                    author_id=comment_author.id,
                    parent_comment_id=None,
                    body_markdown=make_comment_body(fixture=fixture, index=index),
                    status=CommentStatus.ACTIVE,
                    depth=0,
                    upvote_count=comment_score,
                    downvote_count=0,
                    score=comment_score,
                    rank_score=float(comment_score),
                    created_at=comment_created_at,
                    updated_at=comment_created_at,
                )
            )


async def main() -> None:
    fixtures = load_fixture()
    async with get_session_factory()() as db:
        for fixture in fixtures:
            await seed_post(db=db, fixture=fixture)

        author_names = {fixture.author for fixture in fixtures}
        for fixture in fixtures:
            stack = list(fixture.threaded_comments)
            while stack:
                comment = stack.pop()
                author_names.add(comment.author)
                stack.extend(comment.replies)
        for username in author_names:
            user = await db.scalar(select(User).where(User.username == username))
            if user is None:
                continue
            user.last_active_at = datetime.now(UTC)
            user.post_count = int(
                (await db.scalar(select(func.count()).select_from(Post).where(Post.author_id == user.id, Post.status == PostStatus.ACTIVE))) or 0
            )
            user.comment_count = int(
                (
                    await db.scalar(
                        select(func.count()).select_from(Comment).where(
                            Comment.author_id == user.id,
                            Comment.status == CommentStatus.ACTIVE,
                        )
                    )
                )
                or 0
            )

        await db.commit()
    await dispose_engine()
    print(f"Seeded {len(fixtures)} development feed posts from {FIXTURE_PATH.name}")


if __name__ == "__main__":
    asyncio.run(main())
