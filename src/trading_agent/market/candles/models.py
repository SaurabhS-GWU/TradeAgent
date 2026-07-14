"""OHLCV candle domain models."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Candle:
    """Completed OHLCV candle for a single symbol and time period.

    ``timestamp`` marks the **start** of the candle period (e.g. 09:30:00 for
    the 09:30–09:31 one-minute bar).
    """

    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

    def __str__(self) -> str:
        return (
            f"CANDLE {self.symbol} @ {self.timestamp.isoformat()} "
            f"O={self.open} H={self.high} L={self.low} C={self.close} V={self.volume}"
        )
