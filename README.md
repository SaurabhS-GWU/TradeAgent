# Trading Agent

An options trading **signal** platform written in Python. It monitors market conditions, calculates indicators, and generates BUY/SELL signals — but **never executes trades automatically**.

## Current status

This repository contains the **project foundation** only: configuration, logging, and a modular package layout. Market data, indicators, signals, notifications, storage, and analytics are planned for future phases (see [PROJECT.md](PROJECT.md)).

## Requirements

- Python 3.12+
- pip

## Setup

1. **Clone the repository** and enter the project directory.

2. **Create and activate a virtual environment:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # macOS / Linux
   # .venv\Scripts\activate    # Windows
   ```

3. **Install dependencies** (editable install so imports work):

   ```bash
   pip install -e .
   ```

   Or install from `requirements.txt` only, then add the package manually:

   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

4. **Configure environment variables:**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` as needed. See `.env.example` for available variables.

## Run

From the project root with your virtual environment activated:

```bash
python main.py
```

Expected output (INFO level):

```
2026-07-04 10:00:00 | INFO     | trading_agent.app | Starting TradingAgent (env=development, log_level=INFO)
2026-07-04 10:00:00 | INFO     | trading_agent.app | Application bootstrap complete. Domain modules not yet wired.
```

## Project layout

```
TradingAgent/
├── main.py                 # Thin entry point
├── src/trading_agent/      # Application package
│   ├── app.py              # Application orchestrator
│   ├── config/             # Settings from environment
│   ├── infrastructure/     # Logging and cross-cutting concerns
│   ├── core/               # Shared types (future)
│   ├── market/             # Market data (future)
│   ├── indicators/         # Indicators (future)
│   ├── signals/            # Signal generation (future)
│   ├── notifications/      # Alerts (future)
│   ├── storage/            # Persistence (future)
│   └── analytics/          # Reporting (future)
├── .env.example
├── requirements.txt
├── pyproject.toml
├── README.md
└── PROJECT.md
```

## Documentation

- [PROJECT.md](PROJECT.md) — architecture, design decisions, and phased roadmap.

## License

Private project. All rights reserved.
