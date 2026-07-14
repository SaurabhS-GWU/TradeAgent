"""Aggregate normalized market updates into OHLCV candles."""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from trading_agent.market.candles.models import Candle
from trading_agent.market.models import MarketUpdate, UpdateType

logger = logging.getLogger(__name__)

_ONE_MINUTE = timedelta(minutes=1)

CandleCallback = Callable[[Candle], None]


@dataclass
class _InProgressCandle:
    """Mutable candle under construction for a single symbol."""

    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

    def apply_trade(self, price: Decimal, size: int) -> None:
        """Incorporate a trade into the active candle."""
        self.high = max(self.high, price)
        self.low = min(self.low, price)
        self.close = price
        self.volume += size

    def finalize(self) -> Candle:
        """Return an immutable snapshot of the completed candle."""
        return Candle(
            symbol=self.symbol,
            timestamp=self.timestamp,
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume,
        )


def _minute_start(timestamp: datetime) -> datetime:
    """Return the start of the one-minute period containing ``timestamp``."""
    return timestamp.replace(second=0, microsecond=0)


class CandleBuilder:
    """Build one-minute OHLCV candles from generic market updates.

    Only trade updates contribute to candles. Quote updates are ignored.
    Each symbol is aggregated independently.
    """

    def __init__(
        self,
        *,
        on_candle_complete: CandleCallback | None = None,
    ) -> None:
        self._on_candle_complete = on_candle_complete
        self._active: dict[str, _InProgressCandle] = {}

    def process(self, update: MarketUpdate) -> Candle | None:
        """Incorporate a market update and return a completed candle, if any.

        When an update falls in a new minute bucket for its symbol, the
        previously active candle is finalized and returned. The incoming
        trade then opens the next candle.

        Args:
            update: Normalized market event from any provider.

        Returns:
            The completed candle when a minute boundary is crossed, otherwise
            ``None``.
        """
        if update.update_type is not UpdateType.TRADE:
            logger.debug("Skipping non-trade update for candle aggregation | %s", update)
            return None

        if update.price is None or update.trade_size is None:
            logger.debug("Skipping trade without price or size | %s", update)
            return None

        period_start = _minute_start(update.timestamp)
        completed = self._advance_symbol(
            symbol=update.symbol,
            period_start=period_start,
            price=update.price,
            size=update.trade_size,
        )

        if completed is not None:
            logger.info("Candle completed | %s", completed)
            if self._on_candle_complete is not None:
                self._on_candle_complete(completed)

        return completed

    def _advance_symbol(
        self,
        *,
        symbol: str,
        period_start: datetime,
        price: Decimal,
        size: int,
    ) -> Candle | None:
        active = self._active.get(symbol)

        if active is None:
            self._active[symbol] = _InProgressCandle(
                symbol=symbol,
                timestamp=period_start,
                open=price,
                high=price,
                low=price,
                close=price,
                volume=size,
            )
            return None

        if period_start < active.timestamp:
            logger.warning(
                "Ignoring late trade for %s at %s (active candle starts %s)",
                symbol,
                period_start.isoformat(),
                active.timestamp.isoformat(),
            )
            return None

        if period_start == active.timestamp:
            active.apply_trade(price, size)
            return None

        completed = active.finalize()
        self._active[symbol] = _InProgressCandle(
            symbol=symbol,
            timestamp=period_start,
            open=price,
            high=price,
            low=price,
            close=price,
            volume=size,
        )
        return completed

    @property
    def interval(self) -> timedelta:
        """Duration of each candle period."""
        return _ONE_MINUTE
