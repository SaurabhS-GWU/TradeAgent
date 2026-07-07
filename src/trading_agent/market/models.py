"""Provider-agnostic market data domain models."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class UpdateType(str, Enum):
    """Kind of market data update."""

    TRADE = "trade"
    QUOTE = "quote"


class ConnectionStatus(str, Enum):
    """Lifecycle state of a market data connection."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    AUTHENTICATED = "authenticated"
    SUBSCRIBED = "subscribed"
    RECONNECTING = "reconnecting"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class MarketUpdate:
    """Normalized market data event from any provider."""

    symbol: str
    update_type: UpdateType
    timestamp: datetime
    price: Decimal | None = None
    trade_size: int | None = None
    bid_price: Decimal | None = None
    ask_price: Decimal | None = None
    bid_size: int | None = None
    ask_size: int | None = None

    def __str__(self) -> str:
        if self.update_type is UpdateType.TRADE:
            return (
                f"TRADE {self.symbol} price={self.price} "
                f"size={self.trade_size} @ {self.timestamp.isoformat()}"
            )
        return (
            f"QUOTE {self.symbol} bid={self.bid_price}x{self.bid_size} "
            f"ask={self.ask_price}x{self.ask_size} @ {self.timestamp.isoformat()}"
        )
