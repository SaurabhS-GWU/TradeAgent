"""Application orchestrator.

Wires together configuration, logging, and (in future phases) domain
services. ``main.py`` delegates here so the entry point stays thin.
"""

import asyncio
import logging
import signal

from trading_agent.config import Settings, load_settings
from trading_agent.infrastructure.logging import setup_logging
from trading_agent.market import MarketDataClient, create_market_data_client

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

        try:
            asyncio.run(self._run_market_data())
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")

    async def _run_market_data(self) -> None:
        """Start the live market data client and shut down cleanly on signals."""
        client = create_market_data_client()
        self._register_shutdown_handlers(client)

        try:
            await client.start()
        except asyncio.CancelledError:
            logger.info("Market data task cancelled")
            raise
        finally:
            await client.stop()

    def _register_shutdown_handlers(self, client: MarketDataClient) -> None:
        """Request a clean client stop when the process receives a shutdown signal."""
        loop = asyncio.get_running_loop()

        def request_shutdown() -> None:
            logger.info("Shutdown signal received; stopping market data client")
            loop.create_task(client.stop())

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, request_shutdown)
            except NotImplementedError:
                # Windows does not support loop signal handlers for SIGTERM.
                logger.debug("Signal handler not registered for %s on this platform", sig.name)
