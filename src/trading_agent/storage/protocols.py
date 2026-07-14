"""Interfaces for swappable storage backends."""

from collections.abc import Sequence
from typing import Protocol

from trading_agent.market.candles.models import Candle


class CandleStorage(Protocol):
    """Contract for storing and retrieving completed OHLCV candles.

    ``CandleStore`` is the in-memory implementation. A database-backed
    adapter can implement this same protocol without changing callers.
    """

    def add(self, candle: Candle) -> None:
        """Persist a completed candle."""

    def latest(self, symbol: str) -> Candle | None:
        """Return the most recent candle for ``symbol``."""

    def last_n(self, symbol: str, n: int) -> Sequence[Candle]:
        """Return up to ``n`` most recent candles for ``symbol``, oldest first."""

    def all(self, symbol: str) -> Sequence[Candle]:
        """Return all stored candles for ``symbol``, oldest first."""
