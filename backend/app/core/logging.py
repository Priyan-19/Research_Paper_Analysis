import logging
import sys
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """
    Configures application-wide logging format, handlers, and log levels.
    """
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Custom log format
    log_format = "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s"

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger("kg_research_assistant")
    logger.setLevel(log_level)
    return logger


logger = setup_logging()
