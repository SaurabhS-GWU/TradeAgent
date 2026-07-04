"""Settings dataclass and environment loading.

Configuration is read from environment variables (via a ``.env`` file in
development). Values are validated once at startup and exposed as an
immutable ``Settings`` object passed through the application.
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_VALID_LOG_LEVELS = frozenset(
    {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"},
)


class Environment(str, Enum):
    """Deployment environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable application settings."""

    app_name: str
    environment: Environment
    log_level: str


def _parse_environment(raw: str) -> Environment:
    normalized = raw.strip().lower()
    try:
        return Environment(normalized)
    except ValueError as exc:
        valid = ", ".join(env.value for env in Environment)
        raise ValueError(
            f"Invalid APP_ENV '{raw}'. Expected one of: {valid}."
        ) from exc


def _parse_log_level(raw: str) -> str:
    normalized = raw.strip().upper()
    if normalized not in _VALID_LOG_LEVELS:
        valid = ", ".join(sorted(_VALID_LOG_LEVELS))
        raise ValueError(
            f"Invalid LOG_LEVEL '{raw}'. Expected one of: {valid}."
        )
    return normalized


def load_settings(env_file: Path | None = None) -> Settings:
    """Load and validate settings from environment variables.

    Args:
        env_file: Optional path to a ``.env`` file. Defaults to ``.env`` in
            the current working directory.

    Returns:
        Validated, immutable ``Settings`` instance.
    """
    load_dotenv(dotenv_path=env_file)

    app_name = os.getenv("APP_NAME", "TradingAgent").strip()
    if not app_name:
        raise ValueError("APP_NAME must not be empty.")

    environment = _parse_environment(os.getenv("APP_ENV", "development"))
    log_level = _parse_log_level(os.getenv("LOG_LEVEL", "INFO"))

    settings = Settings(
        app_name=app_name,
        environment=environment,
        log_level=log_level,
    )

    logger.debug("Loaded settings: %s", settings)
    return settings
