"""Alpaca implementation of the market data provider contract."""

import asyncio
import logging

from alpaca.data.enums import DataFeed
from alpaca.data.models.quotes import Quote
from alpaca.data.models.trades import Trade

from trading_agent.market.models import ConnectionStatus
from trading_agent.market.protocols import StatusHandler, UpdateHandler
from trading_agent.market.providers.alpaca.config import AlpacaSettings
from trading_agent.market.providers.alpaca.mapper import map_quote, map_trade
from trading_agent.market.providers.alpaca.networking import (
    AlpacaLiveStream,
    build_websocket_params,
)

logger = logging.getLogger(__name__)

_MAX_RECONNECT_DELAY_SECONDS = 60.0


class AlpacaMarketDataProvider:
    """Streams live market data from Alpaca."""

    def __init__(self, settings: AlpacaSettings) -> None:
        self._settings = settings
        self._stream: AlpacaLiveStream | None = None
        self._running = False
        self._on_update: UpdateHandler | None = None
        self._on_status: StatusHandler | None = None
        self._status_tasks: set[asyncio.Task[None]] = set()

    async def start(
        self,
        on_update: UpdateHandler,
        on_status: StatusHandler,
    ) -> None:
        """Connect to Alpaca and stream updates until ``stop`` is called."""
        self._on_update = on_update
        self._on_status = on_status
        self._running = True

        reconnect_delay_seconds = 1.0

        while self._running:
            self._stream = self._create_stream()
            self._register_handlers()

            try:
                # Alpaca SDK exposes this lifecycle loop on StockDataStream.
                await self._stream._run_forever()
                break
            except asyncio.CancelledError:
                logger.info("Alpaca market data task cancelled")
                raise
            except Exception as exc:
                if not self._running:
                    break
                await on_status(ConnectionStatus.RECONNECTING, str(exc))
                logger.exception(
                    "Alpaca market data stream failed; retrying in %.1fs",
                    reconnect_delay_seconds,
                )
                await asyncio.sleep(reconnect_delay_seconds)
                reconnect_delay_seconds = min(
                    reconnect_delay_seconds * 2,
                    _MAX_RECONNECT_DELAY_SECONDS,
                )
            finally:
                self._stream = None

    async def stop(self) -> None:
        """Stop the Alpaca stream and cancel pending status callbacks."""
        self._running = False

        if self._stream is not None:
            await self._stream.stop_ws()

        await self._drain_status_tasks()

    def _create_stream(self) -> AlpacaLiveStream:
        feed = DataFeed.IEX if self._settings.feed == "IEX" else DataFeed.SIP

        def emit_status(status: ConnectionStatus, detail: str | None) -> None:
            if self._on_status is None:
                return

            task = asyncio.create_task(self._on_status(status, detail))
            self._status_tasks.add(task)
            task.add_done_callback(self._log_status_task_result)
            task.add_done_callback(self._status_tasks.discard)

        return AlpacaLiveStream(
            api_key=self._settings.api_key,
            secret_key=self._settings.secret_key,
            feed=feed,
            websocket_params=build_websocket_params(),
            on_status=emit_status,
        )

    def _register_handlers(self) -> None:
        if self._stream is None or self._on_update is None:
            raise RuntimeError("Stream handlers cannot be registered before startup.")

        async def trade_handler(trade: Trade) -> None:
            await self._on_update(map_trade(trade))

        async def quote_handler(quote: Quote) -> None:
            await self._on_update(map_quote(quote))

        self._stream.subscribe_trades(trade_handler, *self._settings.symbols)
        self._stream.subscribe_quotes(quote_handler, *self._settings.symbols)

    @staticmethod
    def _log_status_task_result(task: asyncio.Task[None]) -> None:
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            logger.error("Status callback failed", exc_info=exc)

    async def _drain_status_tasks(self) -> None:
        if not self._status_tasks:
            return

        pending = list(self._status_tasks)
        for task in pending:
            task.cancel()

        await asyncio.gather(*pending, return_exceptions=True)
        self._status_tasks.clear()
