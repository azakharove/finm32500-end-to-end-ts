from datetime import datetime, timedelta

from trading_lib.strategies import MovingAverageStrategy
from trading_lib.models import Action, MarketDataPoint

def test_moving_avg_crossover():
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
        )
    ]
    signals = []
    for tick in ticks:
        signals.extend(strategy.generate_signals(tick))

    assert len(signals) == 1
    assert signals[0] == ("AAPL", 10, 110, Action.BUY) 

def test_moving_avg_generate_buy():
    # Use smaller windows for testing
        strategy = MovingAverageStrategy(short_window=3, long_window=5, quantity=100)
        
        # Create price data that will generate a buy signal
        # Start with declining prices, then rising prices to create MA crossover
        ticks = []
        base_time = datetime(2025, 1, 1, 10, 0, 0)
        
        # First 5 prices: declining trend (long MA will be higher)
        prices = [100, 99, 98, 97, 96]
        for i, price in enumerate(prices):
            ticks.append(MarketDataPoint(timestamp=base_time + timedelta(seconds=i), symbol="AAPL", price=price))
        
        # Next 3 prices: rising trend (short MA will catch up and cross above long MA)
        prices = [97, 98, 99]
        for i, price in enumerate(prices):
            ticks.append(MarketDataPoint(timestamp=base_time + timedelta(seconds=i+5), symbol="AAPL", price=price))
        
        # Add a few more prices to ensure we have enough for MA calculation
        prices = [100, 101, 102]
        for i, price in enumerate(prices):
            ticks.append(MarketDataPoint(timestamp=base_time + timedelta(seconds=i+8), symbol="AAPL", price=price))
        
        signals = []
        for tick in ticks:
            signals.extend(strategy.generate_signals(tick))
        
        assert len(signals) == 1
        assert signals[0] == ("AAPL", 100, 100, Action.BUY)