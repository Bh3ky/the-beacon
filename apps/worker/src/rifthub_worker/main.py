from __future__ import annotations

import logging

from rifthub_backend import configure_logging, get_settings

logger = logging.getLogger(__name__)


def run_once() -> None:
    logger.info("Worker no-op job completed")


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("Starting RiftHub worker in %s", settings.environment)
    run_once()


if __name__ == "__main__":
    main()
