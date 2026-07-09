"""Tests for application settings loading."""

import pytest

from trading_agent.config import settings as settings_module
from trading_agent.config.settings import Environment, Settings, load_settings
from trading_agent.core.exceptions import ConfigurationError


@pytest.fixture(autouse=True)
def _ignore_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings_module, "load_dotenv", lambda *args, **kwargs: False)


def test_load_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    settings = load_settings()

    assert settings == Settings(
        app_name="TradingAgent",
        environment=Environment.DEVELOPMENT,
        log_level="INFO",
    )


def test_load_settings_custom_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_NAME", "TestAgent")
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("LOG_LEVEL", "debug")

    settings = load_settings()

    assert settings.app_name == "TestAgent"
    assert settings.environment is Environment.PRODUCTION
    assert settings.log_level == "DEBUG"


@pytest.mark.parametrize(
    ("env_value", "message"),
    [
        ("", "APP_NAME must not be empty."),
        ("   ", "APP_NAME must not be empty."),
    ],
)
def test_load_settings_rejects_empty_app_name(
    monkeypatch: pytest.MonkeyPatch,
    env_value: str,
    message: str,
) -> None:
    monkeypatch.setenv("APP_NAME", env_value)

    with pytest.raises(ConfigurationError, match=message):
        load_settings()


def test_load_settings_rejects_invalid_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "local")

    with pytest.raises(ConfigurationError, match="Invalid APP_ENV"):
        load_settings()


def test_load_settings_rejects_invalid_log_level(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LOG_LEVEL", "VERBOSE")

    with pytest.raises(ConfigurationError, match="Invalid LOG_LEVEL"):
        load_settings()
