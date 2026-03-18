from sqlalchemy import ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import configure_mappers
from sqlalchemy.schema import CreateIndex, CreateTable

import rifthub_backend.models  # noqa: F401
from rifthub_backend.db.base import Base
from rifthub_backend.db.types import ALL_ENUM_TYPES, UserStatus


def test_metadata_contains_phase_two_tables() -> None:
    assert {
        "users",
        "domains",
        "sources",
        "posts",
        "comments",
        "post_votes",
        "comment_votes",
        "flags",
        "moderation_actions",
        "ingestion_items",
        "user_sessions",
    }.issubset(Base.metadata.tables.keys())


def test_metadata_contains_phase_three_auth_tables() -> None:
    assert "user_verification_tokens" in Base.metadata.tables


def test_required_enum_names_are_registered() -> None:
    assert {enum_type.name for enum_type in ALL_ENUM_TYPES} == {
        "user_role_enum",
        "user_status_enum",
        "post_type_enum",
        "post_status_enum",
        "comment_status_enum",
        "category_enum",
        "flag_target_type_enum",
        "flag_status_enum",
        "flag_reason_enum",
        "moderation_target_type_enum",
        "moderation_action_type_enum",
        "source_type_enum",
        "source_status_enum",
        "ingestion_status_enum",
    }


def test_user_status_enum_includes_pending() -> None:
    assert UserStatus.PENDING.value in next(
        enum_type.enums for enum_type in ALL_ENUM_TYPES if enum_type.name == "user_status_enum"
    )


def test_metadata_compiles_for_postgresql() -> None:
    dialect = postgresql.dialect()

    for table in Base.metadata.sorted_tables:
        assert str(CreateTable(table).compile(dialect=dialect))
        for index in table.indexes:
            assert str(CreateIndex(index).compile(dialect=dialect))


def test_sqlalchemy_mappers_configure_successfully() -> None:
    configure_mappers()


def test_partial_indexes_are_present() -> None:
    flags = Base.metadata.tables["flags"]
    ingestion_items = Base.metadata.tables["ingestion_items"]
    posts = Base.metadata.tables["posts"]

    flags_index = next(index for index in flags.indexes if index.name == "uq_flags_open_reporter_target_reason")
    ingestion_index = next(
        index
        for index in ingestion_items.indexes
        if index.name == "uq_ingestion_items_source_id_external_id"
    )
    posts_index = next(index for index in posts.indexes if index.name == "uq_posts_active_link_url_normalized")

    assert flags_index.unique is True
    assert flags_index.dialect_options["postgresql"]["where"] is not None
    assert ingestion_index.unique is True
    assert ingestion_index.dialect_options["postgresql"]["where"] is not None
    assert posts_index.unique is True
    assert posts_index.dialect_options["postgresql"]["where"] is not None


def test_user_verification_token_indexes_are_present() -> None:
    verification_tokens = Base.metadata.tables["user_verification_tokens"]
    index_names = {index.name for index in verification_tokens.indexes}
    active_token_index = next(
        index
        for index in verification_tokens.indexes
        if index.name == "uq_user_verification_tokens_active_user_id"
    )

    assert "ix_user_verification_tokens_user_id" in index_names
    assert "ix_user_verification_tokens_expires_at" in index_names
    assert active_token_index.unique is True
    assert active_token_index.dialect_options["postgresql"]["where"] is not None


def test_user_counter_constraints_are_present() -> None:
    users = Base.metadata.tables["users"]
    constraint_names = {constraint.name for constraint in users.constraints}

    assert "ck_users_post_count_non_negative" in constraint_names
    assert "ck_users_comment_count_non_negative" in constraint_names


def test_users_status_defaults_to_pending() -> None:
    users = Base.metadata.tables["users"]
    status = users.c.status

    assert status.default is not None
    assert status.default.arg is UserStatus.PENDING
    assert status.server_default is not None
    assert "'pending'" in str(status.server_default.arg)


def test_domain_counter_constraints_are_present() -> None:
    domains = Base.metadata.tables["domains"]
    constraint_names = {constraint.name for constraint in domains.constraints}

    assert "ck_domains_submission_count_non_negative" in constraint_names
    assert "ck_domains_published_post_count_non_negative" in constraint_names


def test_comment_parent_integrity_constraints_are_present() -> None:
    comments = Base.metadata.tables["comments"]
    constraint_names = {constraint.name for constraint in comments.constraints}

    assert "ck_comments_parent_comment_not_self" in constraint_names
    assert any(
        isinstance(constraint, UniqueConstraint)
        and tuple(column.name for column in constraint.columns) == ("id", "post_id")
        for constraint in comments.constraints
    )
    assert any(
        isinstance(constraint, ForeignKeyConstraint)
        and tuple(element.parent.name for element in constraint.elements)
        == ("parent_comment_id", "post_id")
        and tuple(element.column.table.name for element in constraint.elements)
        == ("comments", "comments")
        and tuple(element.column.name for element in constraint.elements) == ("id", "post_id")
        for constraint in comments.constraints
    )


def test_flag_review_state_constraint_is_present() -> None:
    flags = Base.metadata.tables["flags"]
    constraint_names = {constraint.name for constraint in flags.constraints}

    assert "ck_flags_review_state_coherent" in constraint_names


def test_post_counter_and_ingestion_constraints_are_present() -> None:
    posts = Base.metadata.tables["posts"]
    constraint_names = {constraint.name for constraint in posts.constraints}

    assert "ck_posts_bookmark_count_nonnegative" in constraint_names
    assert "ck_posts_view_count_nonnegative" in constraint_names
    assert "ck_posts_ingestion_fields_coherent" in constraint_names
