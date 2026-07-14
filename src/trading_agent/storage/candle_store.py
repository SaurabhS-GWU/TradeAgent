"""In-memory rolling storage for completed OHLCV candles."""

import logging
from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass, field

from trading_agent.market.candles.models import Candle

logger = logging.getLogger(__name__)

DEFAULT_MAX_CANDLES = 500


@dataclass
class CandleStore:
    """Rolling in-memory buffer of completed candles keyed by symbol.

    Each symbol maintains its own fixed-size deque. When capacity is exceeded,
    the oldest candle for that symbol is discarded automatically.
    """

    max_size: int = DEFAULT_MAX_CANDLES
    _candles_by_symbol: dict[str, deque[Candle]] = field(default_factory=dict, init=False)

    def add(self, candle: Candle) -> None:
        """Store a completed candle, discarding the oldest when at capacity."""
        buffer = self._candles_by_symbol.get(candle.symbol)
        if buffer is None:
            buffer = deque(maxlen=self.max_size)
            self._candles_by_symbol[candle.symbol] = buffer

        if len(buffer) == self.max_size:
            discarded = buffer[0]
            logger.debug(
                "Rolling candle buffer full for %s; discarding oldest candle @ %s",
                candle.symbol,
                discarded.timestamp.isoformat(),
            )

        buffer.append(candle)
        logger.debug("Stored candle | %s", candle)

    def latest(self, symbol: str) -> Candle | None:
        """Return the most recent candle for ``symbol``, or ``None`` if empty."""
        buffer = self._candles_by_symbol.get(symbol)
        if not buffer:
            return None
        return buffer[-1]

    def last_n(self, symbol: str, n: int) -> tuple[Candle, ...]:
        """Return up to ``n`` most recent candles for ``symbol``, oldest first."""
        if n <= 0:
            return ()

        buffer = self._candles_by_symbol.get(symbol)
        if not buffer:
            return ()

        return tuple(buffer)[-n:]

    def all(self, symbol: str) -> tuple[Candle, ...]:
        """Return every stored candle for ``symbol``, oldest first."""
        buffer = self._candles_by_symbol.get(symbol)
        if not buffer:
            return ()
        return tuple(buffer)

    def symbols(self) -> tuple[str, ...]:
        """Return symbols that currently have stored candles."""
        return tuple(self._candles_by_symbol)

    def count(self, symbol: str) -> int:
        """Return how many candles are stored for ``symbol``."""
        buffer = self._candles_by_symbol.get(symbol)
        return len(buffer) if buffer else 0
