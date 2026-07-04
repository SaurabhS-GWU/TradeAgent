"""Application entry point.

This module only bootstraps the application. All orchestration lives in
``trading_agent.app``.
"""

from trading_agent.app import Application


def main() -> None:
    """Start the trading signal platform."""
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
