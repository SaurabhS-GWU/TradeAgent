"""Alpaca-specific configuration loaded from environment variables."""

import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

from trading_agent.core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

_VALID_FEEDS = frozenset({"IEX", "SIP"})


@dataclass(frozen=True, slots=True)
class AlpacaSettings:
    """Immutable Alpaca API and subscription settings."""

    api_key: str
    secret_key: str
    feed: str
    symbols: tuple[str, ...]


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigurationError(f"{name} must be set in the environment.")
    return value


def _parse_feed(raw: str) -> str:
    normalized = raw.strip().upper()
    if normalized not in _VALID_FEEDS:
        valid = ", ".join(sorted(_VALID_FEEDS))
        raise ConfigurationError(
            f"Invalid ALPACA_DATA_FEED '{raw}'. Expected one of: {valid}."
        )
    return normalized


def _parse_symbols(raw: str) -> tuple[str, ...]:
    symbols = tuple(
        symbol.strip().upper()
        for symbol in raw.split(",")
        if symbol.strip()
    )
    if not symbols:
        raise ConfigurationError(
            "MARKET_DATA_SYMBOLS must contain at least one symbol."
        )
    return symbols


def load_alpaca_settings() -> AlpacaSettings:
    """Load Alpaca settings from environment variables.

    Raises:
        ConfigurationError: If required values are missing or invalid.
    """
    load_dotenv()

    settings = AlpacaSettings(
        api_key=_require_env("ALPACA_API_KEY"),
        secret_key=_require_env("ALPACA_SECRET_KEY"),
        feed=_parse_feed(os.getenv("ALPACA_DATA_FEED", "IEX")),
        symbols=_parse_symbols(os.getenv("MARKET_DATA_SYMBOLS", "SPY")),
    )

    logger.debug(
        "Loaded Alpaca settings for symbols=%s feed=%s",
        settings.symbols,
        settings.feed,
    )
    return settings
