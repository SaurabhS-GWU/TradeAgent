"""Alpaca WebSocket networking with explicit connection status reporting."""

import asyncio
import logging
import ssl
from collections.abc import Callable

import certifi
import websockets
from alpaca.data.live import StockDataStream

from trading_agent.market.models import ConnectionStatus

logger = logging.getLogger(__name__)

StatusCallback = Callable[[ConnectionStatus, str | None], None]
_RECONNECT_DELAY_SECONDS = 1.0


def build_websocket_ssl_context() -> ssl.SSLContext:
    """Build an SSL context using certifi's CA bundle.

    Python installs from python.org on macOS do not use the system
    keychain by default, which causes CERTIFICATE_VERIFY_FAILED errors
    when opening secure websockets unless a CA bundle is supplied.
    """
    return ssl.create_default_context(cafile=certifi.where())


def build_websocket_params() -> dict[str, ssl.SSLContext]:
    """Return websocket connection parameters for Alpaca streams."""
    return {"ssl": build_websocket_ssl_context()}


class AlpacaLiveStream(StockDataStream):
    """Alpaca stock stream that reports connection lifecycle events."""

    def __init__(
        self,
        *args: object,
        on_status: StatusCallback,
        **kwargs: object,
    ) -> None:
        self._on_status = on_status
        self._ever_connected = False
        super().__init__(*args, **kwargs)

    async def _start_ws(self) -> None:
        if self._ever_connected:
            self._on_status(ConnectionStatus.RECONNECTING, None)

        self._on_status(ConnectionStatus.CONNECTING, None)
        await self._connect()
        await self._auth()

        self._ever_connected = True
        self._on_status(ConnectionStatus.AUTHENTICATED, None)
        logger.info("Alpaca market data stream authenticated")

    async def _send_subscribe_msg(self) -> None:
        await super()._send_subscribe_msg()
        self._on_status(ConnectionStatus.SUBSCRIBED, None)

    async def close(self) -> None:
        await super().close()
        self._on_status(ConnectionStatus.DISCONNECTED, None)

    async def _run_forever(self) -> None:
        """Run the stream with Alpaca's built-in reconnect loop and status hooks."""
        self._loop = asyncio.get_running_loop()

        while not any(
            handlers
            for channel, handlers in self._handlers.items()
            if channel not in ("cancelErrors", "corrections") and handlers
        ):
            if not self._stop_stream_queue.empty():
                self._stop_stream_queue.get(timeout=1)
                self._on_status(ConnectionStatus.STOPPED, None)
                return
            await asyncio.sleep(0)

        logger.info("Starting Alpaca market data stream")
        self._should_run = True
        self._running = False

        while True:
            try:
                if not self._should_run:
                    self._on_status(ConnectionStatus.STOPPED, None)
                    return
                if not self._running:
                    await self._start_ws()
                    await self._send_subscribe_msg()
                    self._running = True
                await self._consume()
            except websockets.WebSocketException as exc:
                await self.close()
                self._running = False
                self._on_status(ConnectionStatus.RECONNECTING, str(exc))
                logger.warning(
                    "Alpaca websocket error, reconnecting in %.1fs: %s",
                    _RECONNECT_DELAY_SECONDS,
                    exc,
                )
                await asyncio.sleep(_RECONNECT_DELAY_SECONDS)
            except ssl.SSLError as exc:
                await self.close()
                self._running = False
                self._on_status(ConnectionStatus.RECONNECTING, str(exc))
                logger.warning(
                    "Alpaca SSL error, reconnecting in %.1fs: %s",
                    _RECONNECT_DELAY_SECONDS,
                    exc,
                )
                await asyncio.sleep(_RECONNECT_DELAY_SECONDS)
            except ValueError as exc:
                if "insufficient subscription" in str(exc):
                    await self.close()
                    self._running = False
                    self._on_status(ConnectionStatus.ERROR, str(exc))
                    logger.exception("Alpaca subscription error: %s", exc)
                    return
                await self.close()
                self._running = False
                self._on_status(ConnectionStatus.RECONNECTING, str(exc))
                logger.warning(
                    "Alpaca connection error, reconnecting in %.1fs: %s",
                    _RECONNECT_DELAY_SECONDS,
                    exc,
                )
                await asyncio.sleep(_RECONNECT_DELAY_SECONDS)
            except Exception as exc:
                await self.close()
                self._running = False
                self._on_status(ConnectionStatus.RECONNECTING, str(exc))
                logger.exception(
                    "Alpaca stream error, reconnecting in %.1fs: %s",
                    _RECONNECT_DELAY_SECONDS,
                    exc,
                )
                await asyncio.sleep(_RECONNECT_DELAY_SECONDS)
