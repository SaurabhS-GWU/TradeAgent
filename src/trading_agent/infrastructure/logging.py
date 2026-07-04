"""Centralized logging configuration.

All modules should use ``logging.getLogger(__name__)`` after
``setup_logging`` has been called once at application startup.
"""

import logging
import sys

from trading_agent.config.settings import Settings


def setup_logging(settings: Settings) -> None:
    """Configure the root logger for the application.

    Args:
        settings: Application settings containing the desired log level.
    """
    log_level = getattr(logging, settings.log_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    logging.getLogger("trading_agent").setLevel(log_level)
