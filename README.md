# End-to-End Trading System

A complete trading system with backtesting, live trading, performance tracking, and order management.

## Quick Start

### Backtesting

Run a backtest by editing `config_simulation.json` and running:

```bash
python main.py --config config_simulation.json
```

Change the `strategy` section in the config to test different strategies. Performance report is automatically saved to `reports/backtest_report_YYYYMMDD_HHMMSS.md`.

**Strategy Optimization:**

```bash
python examples/strategy_optimization.py
```

Tests multiple strategy configurations and compares results programmatically.

### Live Trading

Run the trading system with live Alpaca API:

```bash
python main.py --config config_live.json
```

**Requirements:** Set `ALPACA_API_KEY` and `ALPACA_API_SECRET` environment variables.

## Configuration

### Simulation Config (`config_simulation.json`)

```json
{
  "gateway": {
    "mode": "simulation",
    "csv_path": "AAPL_5d_1m.csv",
    "data_dir": "data"
  },
  "strategy": {
    "type": "rsi",
    "period": 14,
    "oversold": 30,
    "overbought": 70,
    "quantity": 10
  },
  "initial_capital": 100000.0,
  "max_orders_per_minute": 60,
  "max_order_value": 50000.0
}
```

### Live Config (`config_live.json`)

```json
{
  "gateway": {
    "mode": "live",
    "api_key": "${ALPACA_API_KEY}",
    "api_secret": "${ALPACA_API_SECRET}",
    "base_url": "https://paper-api.alpaca.markets",
    "symbols": ["AAPL", "MSFT"]
  },
  "strategy": {
    "type": "rsi",
    "period": 14,
    "oversold": 30,
    "overbought": 70,
    "quantity": 10
  }
}
```

### Available Strategies

**RSI Strategy:**
```json
{
  "type": "rsi",
  "period": 14,
  "oversold": 30,
  "overbought": 70,
  "quantity": 10
}
```

**Moving Average Strategy:**
```json
{
  "type": "moving_average",
  "short_window": 5,
  "long_window": 20,
  "quantity": 10
}
```

To test different strategies, just change the `strategy` section in your config file and run:
```bash
python main.py --config config_simulation.json
```

## Performance Reports

Performance reports are automatically generated in `reports/` directory as markdown files containing:

- Summary metrics (returns, P&L)
- Trade statistics (win rate, profit factor)
- Risk metrics (drawdown, Sharpe ratio)
- **Equity curve graph** (visual chart of portfolio value over time)
- Equity curve data table
- Trade history

## Testing

Run all tests:

```bash
python -m pytest tests/ -v
```

Run specific test suites:

```bash
python -m pytest tests/performance_test.py -v
python -m pytest tests/order_manager_test.py -v
python -m pytest tests/engine_order_test.py -v
```

## Project Structure

```
trading_lib/
├── performance.py       # Performance tracking & metrics
├── engine.py            # Trading engine orchestrator
├── order_manager.py     # Order validation & tracking
├── portfolio/           # Portfolio management
├── strategies/          # Trading strategies
├── gateway/             # Market data & execution (live/sim)
└── models.py            # Data models

examples/
├── backtest_example.py  # Example: programmatic backtest
├── strategy_optimization.py  # Example: test multiple strategies
└── ...

tests/
├── performance_test.py  # Performance tracking tests
├── engine_order_test.py # Engine order handling tests
└── ...
```

## Features

- **Backtesting**: Test strategies on historical data
- **Live Trading**: Connect to Alpaca API for paper/live trading
- **Performance Tracking**: Automatic metrics calculation (Sharpe, drawdown, win rate, etc.)
- **Order Management**: Validation, rate limiting, position tracking
- **Partial Fills**: Track and handle partial order fills
- **Market Data Logging**: Save live market data to CSV for later backtesting
