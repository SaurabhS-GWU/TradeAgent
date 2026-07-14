"""Tests for OHLCV candle models."""

from datetime import datetime, timezone
from decimal import Decimal

from trading_agent.market.candles.models import Candle


def test_candle_str() -> None:
    candle = Candle(
        symbol="SPY",
        timestamp=datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc),
        open=Decimal("450.00"),
        high=Decimal("451.00"),
        low=Decimal("449.50"),
        close=Decimal("450.25"),
        volume=100,
    )

    rendered = str(candle)

    assert "CANDLE SPY" in rendered
    assert "O=450.00" in rendered
    assert "H=451.00" in rendered
    assert "L=449.50" in rendered
    assert "C=450.25" in rendered
    assert "V=100" in rendered
