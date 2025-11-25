"""Example demonstrating market data logging from live trading."""

import sys
from pathlib import Path

# Add parent directory to path so we can import trading_lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from trading_lib.models import MarketDataPoint
from trading_lib.market_data_logger import MarketDataLogger

# Create logger (will create data/live/ directory)
logger = MarketDataLogger(data_dir="data/live")

# Simulate some ticks
ticks = [
    MarketDataPoint(timestamp=datetime.now(), symbol="AAPL", price=175.50),
    MarketDataPoint(timestamp=datetime.now(), symbol="AAPL", price=175.52),
    MarketDataPoint(timestamp=datetime.now(), symbol="MSFT", price=372.30),
    MarketDataPoint(timestamp=datetime.now(), symbol="MSFT", price=372.35),
]

# Log each tick (will create files automatically)
for tick in ticks:
    logger.log_tick(tick)
    print(f"Logged: {tick.symbol} @ ${tick.price:.2f}")

# Close all files
logger.close_all()

print("\nFiles created:")
print(f"  - {logger.get_filepath('AAPL')}")
print(f"  - {logger.get_filepath('MSFT')}")

"""
Output structure:
data/live/
├── AAPL/
│   └── AAPL_20231125.csv
└── MSFT/
    └── MSFT_20231125.csv

Each CSV contains:
Datetime,Symbol,Close
2023-11-25T17:30:00,AAPL,175.50
2023-11-25T17:30:01,AAPL,175.52
...

When running LiveGateway:
- Market data is automatically saved as it arrives
- Files rotate daily (one file per symbol per day)
- Organized by: data/live/{SYMBOL}/{SYMBOL}_{YYYYMMDD}.csv
- Can be used later for backtesting with SimulationGateway
"""

