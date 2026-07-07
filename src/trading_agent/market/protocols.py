"""Interfaces for swappable market data providers."""

from collections.abc import Awaitable, Callable
from typing import Protocol

from trading_agent.market.models import ConnectionStatus, MarketUpdate

UpdateHandler = Callable[[MarketUpdate], Awaitable[None]]
StatusHandler = Callable[[ConnectionStatus, str | None], Awaitable[None]]


class MarketDataProvider(Protocol):
    """Contract implemented by live market data backends."""

    async def start(
        self,
        on_update: UpdateHandler,
        on_status: StatusHandler,
    ) -> None:
        """Connect, subscribe, and deliver updates until stopped."""

    async def stop(self) -> None:
        """Stop streaming and release network resources."""
