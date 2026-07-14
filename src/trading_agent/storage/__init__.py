"""Signal and candle persistence."""

from trading_agent.storage.candle_store import DEFAULT_MAX_CANDLES, CandleStore
from trading_agent.storage.protocols import CandleStorage

__all__ = [
    "CandleStorage",
    "CandleStore",
    "DEFAULT_MAX_CANDLES",
]
