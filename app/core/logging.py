"""Loguru logging setup for the application."""

import sys
from pathlib import Path

from loguru import logger


def setup_logging(
    level: str = "INFO",
    log_to_file: bool = False,
    log_file: str | None = None,
) -> logger:  # type: ignore[type-arg]
    """Configure loguru with stdout and optional file sink.

    Args:
        level: Minimum log level (DEBUG, INFO, WARNING, ERROR).
        log_to_file: Whether to also write logs to a file.
        log_file: Path to the log file (required when log_to_file is True).
    """
    logger.remove()
    logger.add(
        sys.stdout, level=level, backtrace=False, diagnose=False, enqueue=True
    )
    if log_to_file and log_file:
        p = Path(log_file)
        p.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            str(p),
            level=level,
            rotation="10 MB",
            retention="14 days",
            enqueue=True,
            backtrace=False,
            diagnose=False,
        )
    return logger
