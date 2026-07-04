"""Application orchestrator.

Wires together configuration, logging, and (in future phases) domain
services. ``main.py`` delegates here so the entry point stays thin.
"""

import logging

from trading_agent.config import Settings, load_settings
from trading_agent.infrastructure.logging import setup_logging

logger = logging.getLogger(__name__)


class Application:
    """Bootstrap and run the trading signal platform."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or load_settings()

    @property
    def settings(self) -> Settings:
        return self._settings

    def run(self) -> None:
        """Initialize infrastructure and start the application."""
        setup_logging(self._settings)

        logger.info(
            "Starting %s (env=%s, log_level=%s)",
            self._settings.app_name,
            self._settings.environment.value,
            self._settings.log_level,
        )

        logger.info("Application bootstrap complete. Domain modules not yet wired.")
