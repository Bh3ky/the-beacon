from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    environment: str = "development"
    log_level: str = "INFO"
    api_host: str = "127.0.0.1"
    api_port: int = 8000


def get_settings() -> Settings:
    return Settings(
        environment=os.getenv("RIFTHUB_ENV", "development"),
        log_level=os.getenv("RIFTHUB_LOG_LEVEL", "INFO").upper(),
        api_host=os.getenv("RIFTHUB_API_HOST", "127.0.0.1"),
        api_port=int(os.getenv("RIFTHUB_API_PORT", "8000")),
    )
