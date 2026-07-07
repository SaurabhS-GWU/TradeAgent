"""Provider-agnostic market data client."""

import asyncio
import logging
import os
from collections.abc import AsyncIterator, Awaitable, Callable

from trading_agent.market.models import ConnectionStatus, MarketUpdate
from trading_agent.market.protocols import MarketDataProvider
from trading_agent.market.providers.alpaca.config import load_alpaca_settings
from trading_agent.market.providers.alpaca.provider import AlpacaMarketDataProvider

logger = logging.getLogger(__name__)

UpdateConsumer = Callable[[MarketUpdate], Awaitable[None] | None]


class MarketDataClient:
    """Public interface for receiving live market data updates."""

    def __init__(self, provider: MarketDataProvider) -> None:
        self._provider = provider
        self._updates: asyncio.Queue[MarketUpdate | None] = asyncio.Queue()
        self._consumers: list[UpdateConsumer] = []

    def add_consumer(self, consumer: UpdateConsumer) -> None:
        """Register a callback invoked for every market update."""
        self._consumers.append(consumer)

    async def updates(self) -> AsyncIterator[MarketUpdate]:
        """Async iterator over normalized market updates."""
        while True:
            update = await self._updates.get()
            if update is None:
                break
            yield update

    async def start(self) -> None:
        """Start streaming market data until ``stop`` is called."""
        logger.info("Starting market data client")
        await self._provider.start(self._handle_update, self._handle_status)

    async def stop(self) -> None:
        """Stop streaming and close the provider connection."""
        logger.info("Stopping market data client")
        await self._provider.stop()
        await self._updates.put(None)

    async def _handle_update(self, update: MarketUpdate) -> None:
        logger.info("Market update received | %s", update)
        await self._updates.put(update)

        for consumer in self._consumers:
            result = consumer(update)
            if asyncio.iscoroutine(result):
                await result

    async def _handle_status(
        self,
        status: ConnectionStatus,
        detail: str | None,
    ) -> None:
        if detail:
            logger.info("Market data connection status | %s | %s", status.value, detail)
        else:
            logger.info("Market data connection status | %s", status.value)


def create_market_data_client() -> MarketDataClient:
    """Build a market data client from environment configuration."""
    provider_name = os.getenv("MARKET_DATA_PROVIDER", "alpaca").strip().lower()

    if provider_name == "alpaca":
        provider: MarketDataProvider = AlpacaMarketDataProvider(load_alpaca_settings())
    else:
        raise ValueError(
            f"Unsupported MARKET_DATA_PROVIDER '{provider_name}'. "
            "Supported providers: alpaca."
        )

    return MarketDataClient(provider)
