from __future__ import annotations

from enum import StrEnum
from typing import Final

from sqlalchemy import Enum


def _values(enum_cls: type[StrEnum]) -> list[str]:
    return [member.value for member in enum_cls]


def _enum_type(enum_cls: type[StrEnum], name: str) -> Enum:
    return Enum(
        enum_cls,
        name=name,
        native_enum=True,
        validate_strings=True,
        values_callable=_values,
    )


class UserRole(StrEnum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class UserStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"


class PostType(StrEnum):
    LINK = "link"
    TEXT = "text"
    JOB = "job"


class PostStatus(StrEnum):
    ACTIVE = "active"
    HIDDEN = "hidden"
    REMOVED = "removed"
    LOCKED = "locked"


class CommentStatus(StrEnum):
    ACTIVE = "active"
    HIDDEN = "hidden"
    REMOVED = "removed"
    LOCKED = "locked"


class Category(StrEnum):
    FUNDING = "funding"
    LAUNCH = "launch"
    POLICY = "policy"
    OPINION = "opinion"
    ASK = "ask"
    SHOW = "show"
    JOBS = "jobs"
    ENGINEERING = "engineering"
    ECOSYSTEM = "ecosystem"


class FlagTargetType(StrEnum):
    POST = "post"
    COMMENT = "comment"
    USER = "user"


class FlagStatus(StrEnum):
    OPEN = "open"
    REVIEWING = "reviewing"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class FlagReason(StrEnum):
    SPAM = "spam"
    ABUSE = "abuse"
    MISINFORMATION = "misinformation"
    OFF_TOPIC = "off_topic"
    OTHER = "other"


class ModerationTargetType(StrEnum):
    POST = "post"
    COMMENT = "comment"
    USER = "user"
    DOMAIN = "domain"
    SOURCE = "source"
    INGESTION_ITEM = "ingestion_item"


class ModerationActionType(StrEnum):
    HIDE = "hide"
    REMOVE = "remove"
    LOCK = "lock"
    UNLOCK = "unlock"
    RESTORE = "restore"
    RECLASSIFY = "reclassify"
    SUSPEND_USER = "suspend_user"
    BAN_USER = "ban_user"
    UNSUSPEND_USER = "unsuspend_user"
    SET_DOMAIN_TRUST = "set_domain_trust"
    BLOCK_DOMAIN = "block_domain"
    UNBLOCK_DOMAIN = "unblock_domain"
    APPROVE_INGESTION = "approve_ingestion"
    REJECT_INGESTION = "reject_ingestion"


class SourceType(StrEnum):
    RSS = "rss"
    MANUAL = "manual"
    SCRAPER = "scraper"
    API = "api"


class SourceStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"


class IngestionStatus(StrEnum):
    DISCOVERED = "discovered"
    NORMALIZED = "normalized"
    DUPLICATE = "duplicate"
    CLASSIFIED = "classified"
    AWAITING_REVIEW = "awaiting_review"
    PUBLISHED = "published"
    REJECTED = "rejected"
    FAILED = "failed"


USER_ROLE_ENUM: Final = _enum_type(UserRole, "user_role_enum")
USER_STATUS_ENUM: Final = _enum_type(UserStatus, "user_status_enum")
POST_TYPE_ENUM: Final = _enum_type(PostType, "post_type_enum")
POST_STATUS_ENUM: Final = _enum_type(PostStatus, "post_status_enum")
COMMENT_STATUS_ENUM: Final = _enum_type(CommentStatus, "comment_status_enum")
CATEGORY_ENUM: Final = _enum_type(Category, "category_enum")
FLAG_TARGET_TYPE_ENUM: Final = _enum_type(FlagTargetType, "flag_target_type_enum")
FLAG_STATUS_ENUM: Final = _enum_type(FlagStatus, "flag_status_enum")
FLAG_REASON_ENUM: Final = _enum_type(FlagReason, "flag_reason_enum")
MODERATION_TARGET_TYPE_ENUM: Final = _enum_type(
    ModerationTargetType,
    "moderation_target_type_enum",
)
MODERATION_ACTION_TYPE_ENUM: Final = _enum_type(
    ModerationActionType,
    "moderation_action_type_enum",
)
SOURCE_TYPE_ENUM: Final = _enum_type(SourceType, "source_type_enum")
SOURCE_STATUS_ENUM: Final = _enum_type(SourceStatus, "source_status_enum")
INGESTION_STATUS_ENUM: Final = _enum_type(IngestionStatus, "ingestion_status_enum")

ALL_ENUM_TYPES: Final[tuple[Enum, ...]] = (
    USER_ROLE_ENUM,
    USER_STATUS_ENUM,
    POST_TYPE_ENUM,
    POST_STATUS_ENUM,
    COMMENT_STATUS_ENUM,
    CATEGORY_ENUM,
    FLAG_TARGET_TYPE_ENUM,
    FLAG_STATUS_ENUM,
    FLAG_REASON_ENUM,
    MODERATION_TARGET_TYPE_ENUM,
    MODERATION_ACTION_TYPE_ENUM,
    SOURCE_TYPE_ENUM,
    SOURCE_STATUS_ENUM,
    INGESTION_STATUS_ENUM,
)
