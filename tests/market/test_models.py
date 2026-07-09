"""Tests for market data domain models."""

from datetime import datetime, timezone
from decimal import Decimal

from trading_agent.market.models import MarketUpdate, UpdateType


def test_market_update_trade_str() -> None:
    update = MarketUpdate(
        symbol="SPY",
        update_type=UpdateType.TRADE,
        timestamp=datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc),
        price=Decimal("450.25"),
        trade_size=100,
    )

    rendered = str(update)

    assert "TRADE SPY" in rendered
    assert "price=450.25" in rendered
    assert "size=100" in rendered


def test_market_update_quote_str() -> None:
    update = MarketUpdate(
        symbol="QQQ",
        update_type=UpdateType.QUOTE,
        timestamp=datetime(2026, 1, 15, 14, 31, tzinfo=timezone.utc),
        bid_price=Decimal("380.10"),
        ask_price=Decimal("380.12"),
        bid_size=200,
        ask_size=150,
    )

    rendered = str(update)

    assert "QUOTE QQQ" in rendered
    assert "bid=380.10x200" in rendered
    assert "ask=380.12x150" in rendered
