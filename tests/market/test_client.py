"""Tests for the provider-agnostic market data client."""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_agent.core.exceptions import ConfigurationError
from trading_agent.market.client import MarketDataClient, create_market_data_client
from trading_agent.market.models import ConnectionStatus, MarketUpdate, UpdateType
from trading_agent.market.protocols import StatusHandler, UpdateHandler


class FakeProvider:
    """Minimal in-memory provider for client lifecycle tests."""

    def __init__(self) -> None:
        self.started = False
        self.stopped = False
        self._on_update: UpdateHandler | None = None
        self._on_status: StatusHandler | None = None
        self._stop_event = asyncio.Event()

    async def start(
        self,
        on_update: UpdateHandler,
        on_status: StatusHandler,
    ) -> None:
        self.started = True
        self._on_update = on_update
        self._on_status = on_status
        await self._stop_event.wait()

    async def stop(self) -> None:
        self.stopped = True
        self._stop_event.set()

    async def emit_update(self, update: MarketUpdate) -> None:
        assert self._on_update is not None
        await self._on_update(update)

    async def emit_status(
        self,
        status: ConnectionStatus,
        detail: str | None = None,
    ) -> None:
        assert self._on_status is not None
        await self._on_status(status, detail)


@pytest.fixture
def sample_update() -> MarketUpdate:
    return MarketUpdate(
        symbol="SPY",
        update_type=UpdateType.TRADE,
        timestamp=datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc),
        price=Decimal("450.25"),
        trade_size=100,
    )


@pytest.mark.asyncio
async def test_client_streams_updates(sample_update: MarketUpdate) -> None:
    provider = FakeProvider()
    client = MarketDataClient(provider)

    async def run_client() -> None:
        await client.start()

    task = asyncio.create_task(run_client())
    await asyncio.sleep(0)
    await provider.emit_update(sample_update)
    await client.stop()
    await task

    received = [update async for update in client.updates()]
    assert received == [sample_update]
    assert provider.started is True
    assert provider.stopped is True


@pytest.mark.asyncio
async def test_client_isolates_consumer_errors(sample_update: MarketUpdate) -> None:
    provider = FakeProvider()
    client = MarketDataClient(provider)
    seen: list[str] = []

    async def failing_consumer(_: MarketUpdate) -> None:
        raise RuntimeError("consumer failed")

    async def healthy_consumer(update: MarketUpdate) -> None:
        seen.append(update.symbol)

    client.add_consumer(failing_consumer)
    client.add_consumer(healthy_consumer)

    async def run_client() -> None:
        await client.start()

    task = asyncio.create_task(run_client())
    await asyncio.sleep(0)
    await provider.emit_update(sample_update)
    await client.stop()
    await task

    assert seen == ["SPY"]


@pytest.mark.asyncio
async def test_client_stop_is_idempotent() -> None:
    provider = FakeProvider()
    client = MarketDataClient(provider)

    async def run_client() -> None:
        await client.start()

    task = asyncio.create_task(run_client())
    await asyncio.sleep(0)
    await client.stop()
    await client.stop()
    await task

    assert provider.stopped is True


def test_create_market_data_client_rejects_unknown_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "unknown")

    with pytest.raises(ConfigurationError, match="Unsupported MARKET_DATA_PROVIDER"):
        create_market_data_client()
