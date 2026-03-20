from .auth import router as auth_router
from .comments import router as comments_router
from .feeds import router as feeds_router
from .flags import router as flags_router
from .posts import router as posts_router
from .stats import router as stats_router

__all__ = ["auth_router", "comments_router", "feeds_router", "flags_router", "posts_router", "stats_router"]
