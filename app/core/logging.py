from pathlib import Path
import sys
from loguru import logger


def setup_logging(level: str = "INFO", log_to_file: bool = False, log_file: str | None = None):
    logger.remove()
    logger.add(sys.stdout, level=level, backtrace=False, diagnose=False, enqueue=True)
    if log_to_file and log_file:
        p = Path(log_file)
        p.parent.mkdir(parents=True, exist_ok=True)
        logger.add(str(p), level=level, rotation="10 MB", retention="14 days", enqueue=True, backtrace=False, diagnose=False)
    return logger
