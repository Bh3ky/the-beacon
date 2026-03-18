"""Initial RiftHub Phase 2 schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260313_01"
down_revision = None
branch_labels = None
depends_on = None


user_role_enum = postgresql.ENUM(
    "user",
    "moderator",
    "admin",
    name="user_role_enum",
    create_type=False,
)
user_status_enum = postgresql.ENUM(
    "pending",
    "active",
    "suspended",
    "banned",
    name="user_status_enum",
    create_type=False,
)
post_type_enum = postgresql.ENUM("link", "text", "job", name="post_type_enum", create_type=False)
post_status_enum = postgresql.ENUM(
    "active",
    "hidden",
    "removed",
    "locked",
    name="post_status_enum",
    create_type=False,
)
comment_status_enum = postgresql.ENUM(
    "active",
    "hidden",
    "removed",
    "locked",
    name="comment_status_enum",
    create_type=False,
)
category_enum = postgresql.ENUM(
    "funding",
    "launch",
    "policy",
    "opinion",
    "ask",
    "show",
    "jobs",
    "engineering",
    "ecosystem",
    name="category_enum",
    create_type=False,
)
flag_target_type_enum = postgresql.ENUM(
    "post",
    "comment",
    "user",
    name="flag_target_type_enum",
    create_type=False,
)
flag_status_enum = postgresql.ENUM(
    "open",
    "reviewing",
    "resolved",
    "dismissed",
    name="flag_status_enum",
    create_type=False,
)
flag_reason_enum = postgresql.ENUM(
    "spam",
    "abuse",
    "misinformation",
    "off_topic",
    "other",
    name="flag_reason_enum",
    create_type=False,
)
moderation_target_type_enum = postgresql.ENUM(
    "post",
    "comment",
    "user",
    "domain",
    "source",
    name="moderation_target_type_enum",
    create_type=False,
)
moderation_action_type_enum = postgresql.ENUM(
    "hide",
    "remove",
    "lock",
    "unlock",
    "restore",
    "reclassify",
    "suspend_user",
    "ban_user",
    "unsuspend_user",
    "set_domain_trust",
    "block_domain",
    "unblock_domain",
    "approve_ingestion",
    "reject_ingestion",
    name="moderation_action_type_enum",
    create_type=False,
)
source_type_enum = postgresql.ENUM(
    "rss",
    "manual",
    "scraper",
    "api",
    name="source_type_enum",
    create_type=False,
)
source_status_enum = postgresql.ENUM(
    "active",
    "paused",
    "disabled",
    name="source_status_enum",
    create_type=False,
)
ingestion_status_enum = postgresql.ENUM(
    "discovered",
    "normalized",
    "duplicate",
    "classified",
    "awaiting_review",
    "published",
    "rejected",
    "failed",
    name="ingestion_status_enum",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()

    for enum_type in (
        user_role_enum,
        user_status_enum,
        post_type_enum,
        post_status_enum,
        comment_status_enum,
        category_enum,
        flag_target_type_enum,
        flag_status_enum,
        flag_reason_enum,
        moderation_target_type_enum,
        moderation_action_type_enum,
        source_type_enum,
        source_status_enum,
        ingestion_status_enum,
    ):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=32), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("role", user_role_enum, server_default=sa.text("'user'"), nullable=False),
        sa.Column("status", user_status_enum, server_default=sa.text("'pending'"), nullable=False),
        sa.Column("karma", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("post_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("comment_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("char_length(username) BETWEEN 3 AND 32", name="username_length"),
        sa.CheckConstraint("username ~ '^[a-z0-9_]+$'", name="username_format"),
        sa.CheckConstraint("post_count >= 0", name="post_count_non_negative"),
        sa.CheckConstraint("comment_count >= 0", name="comment_count_non_negative"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_status", "users", ["status"])
    op.create_index("ix_users_created_at", "users", ["created_at"])

    op.create_table(
        "domains",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("trust_score", sa.Numeric(5, 2), server_default=sa.text("1.00"), nullable=False),
        sa.Column("is_blocked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("submission_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("published_post_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("trust_score > 0", name="trust_score_positive"),
        sa.CheckConstraint("submission_count >= 0", name="submission_count_non_negative"),
        sa.CheckConstraint("published_post_count >= 0", name="published_post_count_non_negative"),
        sa.PrimaryKeyConstraint("id", name="pk_domains"),
        sa.UniqueConstraint("hostname", name="uq_domains_hostname"),
    )
    op.create_index("ix_domains_is_blocked", "domains", ["is_blocked"])
    op.create_index("ix_domains_trust_score", "domains", ["trust_score"])

    op.create_table(
        "sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source_type", source_type_enum, nullable=False),
        sa.Column("status", source_status_enum, server_default=sa.text("'active'"), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("site_url", sa.Text(), nullable=True),
        sa.Column("default_category", category_enum, nullable=True),
        sa.Column("domain_id", sa.Uuid(), nullable=True),
        sa.Column("trust_score", sa.Numeric(5, 2), server_default=sa.text("1.00"), nullable=False),
        sa.Column("auto_publish", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("poll_interval_minutes", sa.Integer(), server_default=sa.text("30"), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("poll_interval_minutes > 0", name="poll_interval_positive"),
        sa.CheckConstraint("trust_score > 0", name="trust_score_positive"),
        sa.ForeignKeyConstraint(["domain_id"], ["domains.id"], name="fk_sources_domain_id_domains"),
        sa.PrimaryKeyConstraint("id", name="pk_sources"),
    )
    op.create_index("ix_sources_status", "sources", ["status"])
    op.create_index("ix_sources_auto_publish", "sources", ["auto_publish"])
    op.create_index("ix_sources_last_checked_at", "sources", ["last_checked_at"])
    op.create_index("ix_sources_domain_id", "sources", ["domain_id"])

    op.create_table(
        "posts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("post_type", post_type_enum, nullable=False),
        sa.Column("category", category_enum, nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("slug", sa.String(length=350), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("url_normalized", sa.Text(), nullable=True),
        sa.Column("domain_id", sa.Uuid(), nullable=True),
        sa.Column("body_markdown", sa.Text(), nullable=True),
        sa.Column("status", post_status_enum, server_default=sa.text("'active'"), nullable=False),
        sa.Column("is_ingested", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("ingested_from_source_id", sa.Uuid(), nullable=True),
        sa.Column("upvote_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("downvote_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("comment_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("score", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("rank_score", sa.Float(), server_default=sa.text("0"), nullable=False),
        sa.Column("bookmark_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("view_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_commented_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("job_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "post_type != 'text' OR (body_markdown IS NOT NULL AND url IS NULL AND url_normalized IS NULL AND domain_id IS NULL)",
            name="text_fields",
        ),
        sa.CheckConstraint(
            "post_type != 'link' OR (url IS NOT NULL AND url_normalized IS NOT NULL AND domain_id IS NOT NULL)",
            name="link_fields",
        ),
        sa.CheckConstraint(
            "post_type != 'job' OR (url IS NOT NULL OR body_markdown IS NOT NULL)",
            name="job_fields",
        ),
        sa.CheckConstraint(
            "(is_ingested = true AND ingested_from_source_id IS NOT NULL) "
            "OR "
            "(is_ingested = false AND ingested_from_source_id IS NULL)",
            name="ingestion_fields_coherent",
        ),
        sa.CheckConstraint("upvote_count >= 0", name="upvote_count_nonnegative"),
        sa.CheckConstraint("downvote_count >= 0", name="downvote_count_nonnegative"),
        sa.CheckConstraint("comment_count >= 0", name="comment_count_nonnegative"),
        sa.CheckConstraint("bookmark_count >= 0", name="bookmark_count_nonnegative"),
        sa.CheckConstraint("view_count >= 0", name="view_count_nonnegative"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], name="fk_posts_author_id_users"),
        sa.ForeignKeyConstraint(["domain_id"], ["domains.id"], name="fk_posts_domain_id_domains"),
        sa.ForeignKeyConstraint(
            ["ingested_from_source_id"],
            ["sources.id"],
            name="fk_posts_ingested_from_source_id_sources",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_posts"),
    )
    op.create_index("ix_posts_author_id", "posts", ["author_id"])
    op.create_index("ix_posts_category", "posts", ["category"])
    op.create_index("ix_posts_post_type", "posts", ["post_type"])
    op.create_index("ix_posts_status", "posts", ["status"])
    op.create_index("ix_posts_submitted_at", "posts", ["submitted_at"])
    op.create_index("ix_posts_rank_score", "posts", ["rank_score"])
    op.create_index("ix_posts_status_rank_score", "posts", ["status", "rank_score"])
    op.create_index(
        "ix_posts_category_status_submitted_at",
        "posts",
        ["category", "status", "submitted_at"],
    )
    op.create_index(
        "ix_posts_post_type_status_submitted_at",
        "posts",
        ["post_type", "status", "submitted_at"],
    )
    op.create_index("ix_posts_domain_id", "posts", ["domain_id"])
    op.create_index("ix_posts_url_normalized", "posts", ["url_normalized"])

    op.create_table(
        "comments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("parent_comment_id", sa.Uuid(), nullable=True),
        sa.Column("body_markdown", sa.Text(), nullable=False),
        sa.Column("status", comment_status_enum, server_default=sa.text("'active'"), nullable=False),
        sa.Column("depth", sa.SmallInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column("upvote_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("downvote_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("score", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("rank_score", sa.Float(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("depth >= 0", name="depth_nonnegative"),
        sa.CheckConstraint("upvote_count >= 0", name="upvote_count_nonnegative"),
        sa.CheckConstraint("downvote_count >= 0", name="downvote_count_nonnegative"),
        sa.CheckConstraint(
            "parent_comment_id IS NULL OR parent_comment_id <> id",
            name="parent_comment_not_self",
        ),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], name="fk_comments_author_id_users"),
        sa.ForeignKeyConstraint(["parent_comment_id"], ["comments.id"], name="fk_comments_parent_comment_id_comments"),
        sa.ForeignKeyConstraint(
            ["parent_comment_id", "post_id"],
            ["comments.id", "comments.post_id"],
            name="fk_comments_parent_comment_id_post_id_comments",
        ),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], name="fk_comments_post_id_posts"),
        sa.PrimaryKeyConstraint("id", name="pk_comments"),
        sa.UniqueConstraint("id", "post_id", name="uq_comments_id_post_id"),
    )
    op.create_index("ix_comments_post_id", "comments", ["post_id"])
    op.create_index("ix_comments_author_id", "comments", ["author_id"])
    op.create_index("ix_comments_parent_comment_id", "comments", ["parent_comment_id"])
    op.create_index("ix_comments_post_id_created_at", "comments", ["post_id", "created_at"])
    op.create_index("ix_comments_post_id_rank_score", "comments", ["post_id", "rank_score"])
    op.create_index(
        "ix_comments_post_id_parent_comment_id",
        "comments",
        ["post_id", "parent_comment_id"],
    )

    op.create_table(
        "post_votes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("vote_value", sa.SmallInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("vote_value IN (-1, 1)", name="vote_value_allowed"),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], name="fk_post_votes_post_id_posts"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_post_votes_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_post_votes"),
    )
    op.create_index("uq_post_votes_post_id_user_id", "post_votes", ["post_id", "user_id"], unique=True)
    op.create_index("ix_post_votes_user_id", "post_votes", ["user_id"])
    op.create_index("ix_post_votes_post_id", "post_votes", ["post_id"])

    op.create_table(
        "comment_votes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("comment_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("vote_value", sa.SmallInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("vote_value IN (-1, 1)", name="vote_value_allowed"),
        sa.ForeignKeyConstraint(
            ["comment_id"],
            ["comments.id"],
            name="fk_comment_votes_comment_id_comments",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_comment_votes_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_comment_votes"),
    )
    op.create_index(
        "uq_comment_votes_comment_id_user_id",
        "comment_votes",
        ["comment_id", "user_id"],
        unique=True,
    )
    op.create_index("ix_comment_votes_user_id", "comment_votes", ["user_id"])
    op.create_index("ix_comment_votes_comment_id", "comment_votes", ["comment_id"])

    op.create_table(
        "flags",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("target_type", flag_target_type_enum, nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("reporter_id", sa.Uuid(), nullable=False),
        sa.Column("reason_code", flag_reason_enum, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", flag_status_enum, server_default=sa.text("'open'"), nullable=False),
        sa.Column("reviewed_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "(status = 'open' AND reviewed_by_user_id IS NULL AND reviewed_at IS NULL) "
            "OR "
            "(status <> 'open' AND reviewed_by_user_id IS NOT NULL AND reviewed_at IS NOT NULL)",
            name="review_state_coherent",
        ),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"], name="fk_flags_reporter_id_users"),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_id"],
            ["users.id"],
            name="fk_flags_reviewed_by_user_id_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_flags"),
    )
    op.create_index("ix_flags_target_type_target_id", "flags", ["target_type", "target_id"])
    op.create_index("ix_flags_reporter_id", "flags", ["reporter_id"])
    op.create_index("ix_flags_status", "flags", ["status"])
    op.create_index("ix_flags_created_at", "flags", ["created_at"])
    op.create_index(
        "uq_flags_open_reporter_target_reason",
        "flags",
        ["reporter_id", "target_type", "target_id", "reason_code"],
        unique=True,
        postgresql_where=sa.text("status = 'open'"),
    )

    op.create_table(
        "moderation_actions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("moderator_id", sa.Uuid(), nullable=False),
        sa.Column("target_type", moderation_target_type_enum, nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("action_type", moderation_action_type_enum, nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["moderator_id"],
            ["users.id"],
            name="fk_moderation_actions_moderator_id_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_moderation_actions"),
    )
    op.create_index("ix_moderation_actions_moderator_id", "moderation_actions", ["moderator_id"])
    op.create_index(
        "ix_moderation_actions_target_type_target_id",
        "moderation_actions",
        ["target_type", "target_id"],
    )
    op.create_index("ix_moderation_actions_action_type", "moderation_actions", ["action_type"])
    op.create_index("ix_moderation_actions_created_at", "moderation_actions", ["created_at"])

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("session_token_hash", sa.String(length=255), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_sessions_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_user_sessions"),
        sa.UniqueConstraint("session_token_hash", name="uq_user_sessions_session_token_hash"),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_expires_at", "user_sessions", ["expires_at"])

    op.create_table(
        "ingestion_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("url_normalized", sa.Text(), nullable=True),
        sa.Column("published_at_external", sa.DateTime(timezone=True), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "ingestion_status",
            ingestion_status_enum,
            server_default=sa.text("'discovered'"),
            nullable=False,
        ),
        sa.Column("detected_category", category_enum, nullable=True),
        sa.Column("linked_post_id", sa.Uuid(), nullable=True),
        sa.Column("dedupe_match_post_id", sa.Uuid(), nullable=True),
        sa.Column("raw_payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("processing_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], name="fk_ingestion_items_source_id_sources"),
        sa.ForeignKeyConstraint(
            ["linked_post_id"],
            ["posts.id"],
            name="fk_ingestion_items_linked_post_id_posts",
        ),
        sa.ForeignKeyConstraint(
            ["dedupe_match_post_id"],
            ["posts.id"],
            name="fk_ingestion_items_dedupe_match_post_id_posts",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ingestion_items"),
    )
    op.create_index("ix_ingestion_items_source_id", "ingestion_items", ["source_id"])
    op.create_index("ix_ingestion_items_ingestion_status", "ingestion_items", ["ingestion_status"])
    op.create_index(
        "ix_ingestion_items_published_at_external",
        "ingestion_items",
        ["published_at_external"],
    )
    op.create_index("ix_ingestion_items_url_normalized", "ingestion_items", ["url_normalized"])
    op.create_index("ix_ingestion_items_linked_post_id", "ingestion_items", ["linked_post_id"])
    op.create_index(
        "uq_ingestion_items_source_id_external_id",
        "ingestion_items",
        ["source_id", "external_id"],
        unique=True,
        postgresql_where=sa.text("external_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_ingestion_items_source_id_external_id", table_name="ingestion_items")
    op.drop_index("ix_ingestion_items_linked_post_id", table_name="ingestion_items")
    op.drop_index("ix_ingestion_items_url_normalized", table_name="ingestion_items")
    op.drop_index("ix_ingestion_items_published_at_external", table_name="ingestion_items")
    op.drop_index("ix_ingestion_items_ingestion_status", table_name="ingestion_items")
    op.drop_index("ix_ingestion_items_source_id", table_name="ingestion_items")
    op.drop_table("ingestion_items")

    op.drop_index("ix_user_sessions_expires_at", table_name="user_sessions")
    op.drop_index("ix_user_sessions_user_id", table_name="user_sessions")
    op.drop_table("user_sessions")

    op.drop_index("ix_moderation_actions_created_at", table_name="moderation_actions")
    op.drop_index("ix_moderation_actions_action_type", table_name="moderation_actions")
    op.drop_index("ix_moderation_actions_target_type_target_id", table_name="moderation_actions")
    op.drop_index("ix_moderation_actions_moderator_id", table_name="moderation_actions")
    op.drop_table("moderation_actions")

    op.drop_index("uq_flags_open_reporter_target_reason", table_name="flags")
    op.drop_index("ix_flags_created_at", table_name="flags")
    op.drop_index("ix_flags_status", table_name="flags")
    op.drop_index("ix_flags_reporter_id", table_name="flags")
    op.drop_index("ix_flags_target_type_target_id", table_name="flags")
    op.drop_table("flags")

    op.drop_index("ix_comment_votes_comment_id", table_name="comment_votes")
    op.drop_index("ix_comment_votes_user_id", table_name="comment_votes")
    op.drop_index("uq_comment_votes_comment_id_user_id", table_name="comment_votes")
    op.drop_table("comment_votes")

    op.drop_index("ix_post_votes_post_id", table_name="post_votes")
    op.drop_index("ix_post_votes_user_id", table_name="post_votes")
    op.drop_index("uq_post_votes_post_id_user_id", table_name="post_votes")
    op.drop_table("post_votes")

    op.drop_index("ix_comments_post_id_parent_comment_id", table_name="comments")
    op.drop_index("ix_comments_post_id_rank_score", table_name="comments")
    op.drop_index("ix_comments_post_id_created_at", table_name="comments")
    op.drop_index("ix_comments_parent_comment_id", table_name="comments")
    op.drop_index("ix_comments_author_id", table_name="comments")
    op.drop_index("ix_comments_post_id", table_name="comments")
    op.drop_table("comments")

    op.drop_index("ix_posts_url_normalized", table_name="posts")
    op.drop_index("ix_posts_domain_id", table_name="posts")
    op.drop_index("ix_posts_post_type_status_submitted_at", table_name="posts")
    op.drop_index("ix_posts_category_status_submitted_at", table_name="posts")
    op.drop_index("ix_posts_status_rank_score", table_name="posts")
    op.drop_index("ix_posts_rank_score", table_name="posts")
    op.drop_index("ix_posts_submitted_at", table_name="posts")
    op.drop_index("ix_posts_status", table_name="posts")
    op.drop_index("ix_posts_post_type", table_name="posts")
    op.drop_index("ix_posts_category", table_name="posts")
    op.drop_index("ix_posts_author_id", table_name="posts")
    op.drop_table("posts")

    op.drop_index("ix_sources_domain_id", table_name="sources")
    op.drop_index("ix_sources_last_checked_at", table_name="sources")
    op.drop_index("ix_sources_auto_publish", table_name="sources")
    op.drop_index("ix_sources_status", table_name="sources")
    op.drop_table("sources")

    op.drop_index("ix_domains_trust_score", table_name="domains")
    op.drop_index("ix_domains_is_blocked", table_name="domains")
    op.drop_table("domains")

    op.drop_index("ix_users_created_at", table_name="users")
    op.drop_index("ix_users_status", table_name="users")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    for enum_type in (
        ingestion_status_enum,
        source_status_enum,
        source_type_enum,
        moderation_action_type_enum,
        moderation_target_type_enum,
        flag_reason_enum,
        flag_status_enum,
        flag_target_type_enum,
        category_enum,
        comment_status_enum,
        post_status_enum,
        post_type_enum,
        user_status_enum,
        user_role_enum,
    ):
        enum_type.drop(bind, checkfirst=True)
