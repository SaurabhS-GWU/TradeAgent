"""Tests for in-memory rolling candle storage."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from trading_agent.market.candles.models import Candle
from trading_agent.storage import CandleStore, DEFAULT_MAX_CANDLES


def _candle(
    *,
    symbol: str = "SPY",
    minute: int,
    close: str = "450.00",
) -> Candle:
    return Candle(
        symbol=symbol,
        timestamp=datetime(2026, 1, 15, 14, minute, tzinfo=timezone.utc),
        open=Decimal("450.00"),
        high=Decimal("451.00"),
        low=Decimal("449.00"),
        close=Decimal(close),
        volume=100,
    )


class TestCandleStore:
    def test_add_and_latest(self) -> None:
        store = CandleStore()
        first = _candle(minute=30)
        second = _candle(minute=31, close="451.00")

        store.add(first)
        store.add(second)

        assert store.latest("SPY") == second

    def test_latest_returns_none_for_unknown_symbol(self) -> None:
        store = CandleStore()

        assert store.latest("SPY") is None

    def test_last_n_returns_oldest_first(self) -> None:
        store = CandleStore()
        candles = [_candle(minute=30 + index, close=f"450.{index}") for index in range(5)]
        for candle in candles:
            store.add(candle)

        result = store.last_n("SPY", 3)

        assert result == tuple(candles[-3:])

    def test_last_n_with_zero_or_negative_returns_empty(self) -> None:
        store = CandleStore()
        store.add(_candle(minute=30))

        assert store.last_n("SPY", 0) == ()
        assert store.last_n("SPY", -1) == ()

    def test_last_n_when_n_exceeds_stored_count(self) -> None:
        store = CandleStore()
        candles = [_candle(minute=30 + index) for index in range(3)]
        for candle in candles:
            store.add(candle)

        assert store.last_n("SPY", 10) == tuple(candles)

    def test_all_returns_entire_collection(self) -> None:
        store = CandleStore()
        candles = [_candle(minute=30 + index) for index in range(4)]
        for candle in candles:
            store.add(candle)

        assert store.all("SPY") == tuple(candles)

    def test_all_returns_empty_for_unknown_symbol(self) -> None:
        store = CandleStore()

        assert store.all("SPY") == ()

    def test_rolling_buffer_discards_oldest_candles(self) -> None:
        store = CandleStore(max_size=3)
        candles = [_candle(minute=30 + index, close=f"450.{index}") for index in range(5)]
        for candle in candles:
            store.add(candle)

        assert store.count("SPY") == 3
        assert store.all("SPY") == tuple(candles[-3:])

    def test_default_capacity_is_500(self) -> None:
        store = CandleStore()
        start = datetime(2026, 1, 15, 9, 30, tzinfo=timezone.utc)

        for index in range(DEFAULT_MAX_CANDLES + 25):
            store.add(
                Candle(
                    symbol="SPY",
                    timestamp=start + timedelta(minutes=index),
                    open=Decimal("450.00"),
                    high=Decimal("451.00"),
                    low=Decimal("449.00"),
                    close=Decimal("450.00"),
                    volume=10,
                ),
            )

        assert store.count("SPY") == DEFAULT_MAX_CANDLES
        assert store.latest("SPY") is not None
        assert store.latest("SPY").timestamp == start + timedelta(minutes=DEFAULT_MAX_CANDLES + 24)
        assert store.all("SPY")[0].timestamp == start + timedelta(minutes=25)

    def test_symbols_are_isolated(self) -> None:
        store = CandleStore()
        spy = _candle(symbol="SPY", minute=30)
        qqq = _candle(symbol="QQQ", minute=30, close="380.00")

        store.add(spy)
        store.add(qqq)

        assert store.latest("SPY") == spy
        assert store.latest("QQQ") == qqq
        assert store.count("SPY") == 1
        assert store.count("QQQ") == 1
        assert set(store.symbols()) == {"SPY", "QQQ"}

    def test_retrieved_sequences_are_copies(self) -> None:
        store = CandleStore()
        store.add(_candle(minute=30))

        first = store.all("SPY")
        second = store.all("SPY")

        assert first == second
        assert first is not second

    def test_candle_store_satisfies_storage_protocol(self) -> None:
        store = CandleStore()
        store.add(_candle(minute=30))

        assert store.latest("SPY") is not None
        assert len(store.last_n("SPY", 1)) == 1
        assert len(store.all("SPY")) == 1
