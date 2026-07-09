"""Tests for Alpaca-to-domain market data mapping."""

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from trading_agent.market.models import UpdateType
from trading_agent.market.providers.alpaca.mapper import map_quote, map_trade


def test_map_trade() -> None:
    trade = SimpleNamespace(
        symbol="SPY",
        timestamp=datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc),
        price=450.25,
        size=100,
    )

    update = map_trade(trade)

    assert update.symbol == "SPY"
    assert update.update_type is UpdateType.TRADE
    assert update.price == Decimal("450.25")
    assert update.trade_size == 100
    assert update.timestamp == trade.timestamp


def test_map_quote() -> None:
    quote = SimpleNamespace(
        symbol="QQQ",
        timestamp=datetime(2026, 1, 15, 14, 31, tzinfo=timezone.utc),
        bid_price=380.10,
        ask_price=380.12,
        bid_size=200,
        ask_size=150,
    )

    update = map_quote(quote)

    assert update.symbol == "QQQ"
    assert update.update_type is UpdateType.QUOTE
    assert update.bid_price == Decimal("380.1")
    assert update.ask_price == Decimal("380.12")
    assert update.bid_size == 200
    assert update.ask_size == 150
