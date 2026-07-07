"""Map Alpaca SDK models to provider-agnostic domain models."""

from decimal import Decimal

from alpaca.data.models.quotes import Quote
from alpaca.data.models.trades import Trade

from trading_agent.market.models import MarketUpdate, UpdateType


def _to_decimal(value: float) -> Decimal:
    return Decimal(str(value))


def map_trade(trade: Trade) -> MarketUpdate:
    """Convert an Alpaca trade event to a ``MarketUpdate``."""
    return MarketUpdate(
        symbol=trade.symbol,
        update_type=UpdateType.TRADE,
        timestamp=trade.timestamp,
        price=_to_decimal(trade.price),
        trade_size=int(trade.size),
    )


def map_quote(quote: Quote) -> MarketUpdate:
    """Convert an Alpaca quote event to a ``MarketUpdate``."""
    return MarketUpdate(
        symbol=quote.symbol,
        update_type=UpdateType.QUOTE,
        timestamp=quote.timestamp,
        bid_price=_to_decimal(quote.bid_price),
        ask_price=_to_decimal(quote.ask_price),
        bid_size=int(quote.bid_size),
        ask_size=int(quote.ask_size),
    )
