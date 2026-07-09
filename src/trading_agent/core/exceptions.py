"""Shared exception types for the trading agent platform."""


class TradingAgentError(Exception):
    """Base exception for recoverable application errors."""


class ConfigurationError(TradingAgentError, ValueError):
    """Raised when environment configuration is invalid or incomplete."""


class MarketDataError(TradingAgentError):
    """Raised when market data streaming encounters a fatal error."""
