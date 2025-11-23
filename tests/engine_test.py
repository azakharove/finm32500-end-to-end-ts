from datetime import datetime
import pytest

from trading_lib.engine import ExecutionEngine
from trading_lib.portfolio import SimplePortfolio
from trading_lib.strategies import MovingAverageStrategy
from trading_lib.models import MarketDataPoint, RecordingInterval


def test_moving_avg_crossover_strategy():
    strategy = MovingAverageStrategy(
        short_window=3, long_window=5, quantity=10
    )
    ticks = [
        MarketDataPoint(
            timestamp=datetime(
                year=2025, month=9, day=21, hour=19, minute=54, second=1
            ),
            symbol="AAPL",
            price=100,
        ),
        MarketDataPoint(
            timestamp=datetime(
                year=2025, month=9, day=21, hour=19, minute=54, second=2
            ),
            symbol="AAPL",
            price=101,
        ),
        MarketDataPoint(
            timestamp=datetime(
                year=2025, month=9, day=21, hour=19, minute=54, second=3
            ),
            symbol="AAPL",
            price=102,
        ),
        MarketDataPoint(
            timestamp=datetime(
                year=2025, month=9, day=21, hour=19, minute=54, second=4
            ),
            symbol="AAPL",
            price=106,
        ),
        MarketDataPoint(
            timestamp=datetime(
                year=2025, month=9, day=21, hour=19, minute=54, second=5
            ),
            symbol="AAPL",
            price=108,
        ),
        MarketDataPoint(
            timestamp=datetime(
                year=2025, month=9, day=21, hour=19, minute=54, second=6
            ),
            symbol="AAPL",
            price=110,
        ),
    ]

    portfolio = SimplePortfolio(holdings={}, cash=10000)
    engine = ExecutionEngine(strategy, portfolio=portfolio)
    engine.process_ticks(ticks)
    assert portfolio.cash == 8900
    assert portfolio.get_holding("AAPL") == {"quantity": 10, "avg_price": 110}

def test_get_period():
    ts = datetime(2024, 3, 15, 14, 27, 33)
    engine = ExecutionEngine(strategy=MovingAverageStrategy(), portfolio=SimplePortfolio())

    engine.recording_interval = RecordingInterval.TICK
    assert engine._get_period(ts) == (ts,)

    engine.recording_interval = RecordingInterval.SECOND
    assert engine._get_period(ts) == (2024, 3, 15, 14, 27, 33)

    engine.recording_interval = RecordingInterval.MINUTE
    assert engine._get_period(ts) == (2024, 3, 15, 14, 27)

    engine.recording_interval = RecordingInterval.HOURLY
    assert engine._get_period(ts) == (2024, 3, 15, 14)

    engine.recording_interval = RecordingInterval.DAILY
    assert engine._get_period(ts) == (2024, 3, 15)

    engine.recording_interval = RecordingInterval.WEEKLY
    year, week, _ = ts.isocalendar()
    assert engine._get_period(ts) == (year, week)

    engine.recording_interval = RecordingInterval.MONTHLY
    assert engine._get_period(ts) == (2024, 3)

    engine.recording_interval = "NOT_A_REAL_INTERVAL"
    with pytest.raises(ValueError, match="Unknown recording interval"):
        engine._get_period(ts)
