"""Tests for one-minute OHLCV candle aggregation."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_agent.market.candles import Candle, CandleBuilder
from trading_agent.market.models import MarketUpdate, UpdateType


def _trade(
    *,
    symbol: str = "SPY",
    timestamp: datetime,
    price: str,
    size: int,
) -> MarketUpdate:
    return MarketUpdate(
        symbol=symbol,
        update_type=UpdateType.TRADE,
        timestamp=timestamp,
        price=Decimal(price),
        trade_size=size,
    )


def _quote(*, symbol: str = "SPY", timestamp: datetime) -> MarketUpdate:
    return MarketUpdate(
        symbol=symbol,
        update_type=UpdateType.QUOTE,
        timestamp=timestamp,
        bid_price=Decimal("100.00"),
        ask_price=Decimal("100.01"),
        bid_size=100,
        ask_size=100,
    )


class TestCandleBuilder:
    def test_first_trade_starts_candle_without_completion(self) -> None:
        builder = CandleBuilder()
        minute = datetime(2026, 1, 15, 14, 30, 12, tzinfo=timezone.utc)

        completed = builder.process(
            _trade(timestamp=minute, price="450.00", size=10),
        )

        assert completed is None

    def test_multiple_trades_in_same_minute_update_ohlcv(self) -> None:
        builder = CandleBuilder()
        base = datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc)

        builder.process(_trade(timestamp=base.replace(second=5), price="450.00", size=10))
        builder.process(_trade(timestamp=base.replace(second=20), price="451.00", size=5))
        builder.process(_trade(timestamp=base.replace(second=45), price="449.50", size=15))

        completed = builder.process(
            _trade(
                timestamp=base.replace(minute=31, second=0),
                price="450.25",
                size=20,
            ),
        )

        assert completed == Candle(
            symbol="SPY",
            timestamp=base,
            open=Decimal("450.00"),
            high=Decimal("451.00"),
            low=Decimal("449.50"),
            close=Decimal("449.50"),
            volume=30,
        )

    def test_new_minute_starts_next_candle(self) -> None:
        builder = CandleBuilder()
        first_minute = datetime(2026, 1, 15, 14, 30, 10, tzinfo=timezone.utc)
        second_minute = datetime(2026, 1, 15, 14, 31, 5, tzinfo=timezone.utc)

        builder.process(_trade(timestamp=first_minute, price="450.00", size=10))
        completed = builder.process(
            _trade(timestamp=second_minute, price="450.50", size=5),
        )

        assert completed == Candle(
            symbol="SPY",
            timestamp=datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc),
            open=Decimal("450.00"),
            high=Decimal("450.00"),
            low=Decimal("450.00"),
            close=Decimal("450.00"),
            volume=10,
        )

        # The trade that triggered rollover belongs to the new candle.
        next_completed = builder.process(
            _trade(
                timestamp=datetime(2026, 1, 15, 14, 32, 0, tzinfo=timezone.utc),
                price="451.00",
                size=1,
            ),
        )

        assert next_completed == Candle(
            symbol="SPY",
            timestamp=datetime(2026, 1, 15, 14, 31, tzinfo=timezone.utc),
            open=Decimal("450.50"),
            high=Decimal("450.50"),
            low=Decimal("450.50"),
            close=Decimal("450.50"),
            volume=5,
        )

    def test_quotes_are_ignored(self) -> None:
        builder = CandleBuilder()
        minute = datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc)

        completed = builder.process(_quote(timestamp=minute))

        assert completed is None

    def test_symbols_are_tracked_independently(self) -> None:
        builder = CandleBuilder()
        minute = datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc)
        next_minute = datetime(2026, 1, 15, 14, 31, tzinfo=timezone.utc)

        builder.process(_trade(symbol="SPY", timestamp=minute, price="450.00", size=10))
        builder.process(_trade(symbol="QQQ", timestamp=minute, price="380.00", size=20))

        spy_completed = builder.process(
            _trade(symbol="SPY", timestamp=next_minute, price="451.00", size=5),
        )
        qqq_completed = builder.process(
            _trade(symbol="QQQ", timestamp=next_minute, price="381.00", size=7),
        )

        assert spy_completed == Candle(
            symbol="SPY",
            timestamp=minute,
            open=Decimal("450.00"),
            high=Decimal("450.00"),
            low=Decimal("450.00"),
            close=Decimal("450.00"),
            volume=10,
        )
        assert qqq_completed == Candle(
            symbol="QQQ",
            timestamp=minute,
            open=Decimal("380.00"),
            high=Decimal("380.00"),
            low=Decimal("380.00"),
            close=Decimal("380.00"),
            volume=20,
        )

    def test_late_trades_are_ignored(self) -> None:
        builder = CandleBuilder()
        first_minute = datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc)
        second_minute = datetime(2026, 1, 15, 14, 31, tzinfo=timezone.utc)

        builder.process(_trade(timestamp=second_minute, price="450.50", size=5))
        completed = builder.process(
            _trade(timestamp=first_minute.replace(second=10), price="449.00", size=99),
        )

        assert completed is None

    def test_on_candle_complete_callback_is_invoked(self) -> None:
        completed_candles: list[Candle] = []
        builder = CandleBuilder(on_candle_complete=completed_candles.append)

        first_minute = datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc)
        second_minute = datetime(2026, 1, 15, 14, 31, tzinfo=timezone.utc)

        builder.process(_trade(timestamp=first_minute, price="450.00", size=10))
        builder.process(_trade(timestamp=second_minute, price="450.50", size=5))

        assert len(completed_candles) == 1
        assert completed_candles[0].volume == 10

    def test_interval_is_one_minute(self) -> None:
        builder = CandleBuilder()

        assert builder.interval.total_seconds() == 60
