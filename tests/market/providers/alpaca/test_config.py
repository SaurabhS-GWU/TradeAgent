"""Tests for Alpaca configuration loading."""

import pytest

from trading_agent.core.exceptions import ConfigurationError
from trading_agent.market.providers.alpaca import config as alpaca_config
from trading_agent.market.providers.alpaca.config import AlpacaSettings, load_alpaca_settings


@pytest.fixture(autouse=True)
def _ignore_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(alpaca_config, "load_dotenv", lambda *args, **kwargs: False)


def test_load_alpaca_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALPACA_API_KEY", "key")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "secret")
    monkeypatch.delenv("ALPACA_DATA_FEED", raising=False)
    monkeypatch.delenv("MARKET_DATA_SYMBOLS", raising=False)

    settings = load_alpaca_settings()

    assert settings == AlpacaSettings(
        api_key="key",
        secret_key="secret",
        feed="IEX",
        symbols=("SPY",),
    )


def test_load_alpaca_settings_parses_symbols(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALPACA_API_KEY", "key")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "secret")
    monkeypatch.setenv("ALPACA_DATA_FEED", "sip")
    monkeypatch.setenv("MARKET_DATA_SYMBOLS", " spy, qqq ,aapl ")

    settings = load_alpaca_settings()

    assert settings.feed == "SIP"
    assert settings.symbols == ("SPY", "QQQ", "AAPL")


@pytest.mark.parametrize("missing_var", ["ALPACA_API_KEY", "ALPACA_SECRET_KEY"])
def test_load_alpaca_settings_requires_credentials(
    monkeypatch: pytest.MonkeyPatch,
    missing_var: str,
) -> None:
    monkeypatch.setenv("ALPACA_API_KEY", "key")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "secret")
    monkeypatch.delenv(missing_var, raising=False)

    with pytest.raises(ConfigurationError, match=f"{missing_var} must be set"):
        load_alpaca_settings()


def test_load_alpaca_settings_rejects_invalid_feed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALPACA_API_KEY", "key")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "secret")
    monkeypatch.setenv("ALPACA_DATA_FEED", "invalid")

    with pytest.raises(ConfigurationError, match="Invalid ALPACA_DATA_FEED"):
        load_alpaca_settings()


def test_load_alpaca_settings_rejects_empty_symbols(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALPACA_API_KEY", "key")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "secret")
    monkeypatch.setenv("MARKET_DATA_SYMBOLS", " , ")

    with pytest.raises(ConfigurationError, match="MARKET_DATA_SYMBOLS"):
        load_alpaca_settings()
