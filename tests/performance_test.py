import pytest
from datetime import datetime

from trading_lib.performance import PerformanceTracker, PerformanceMetrics, Trade, Position
from trading_lib.models import Order, OrderStatus


def test_trade_recording():
    """Test that trades are recorded correctly."""
    tracker = PerformanceTracker(initial_capital=100000.0)
    
    order1 = Order("AAPL", 10, 150.0, OrderStatus.FILLED, filled_quantity=10)
    tracker.record_trade(order1)
    
    assert len(tracker.trades) == 1
    assert tracker.trades[0].symbol == "AAPL"
    assert tracker.trades[0].quantity == 10
    assert tracker.trades[0].price == 150.0
    assert tracker.trades[0].side == "buy"


def test_position_tracking():
    """Test position tracking."""
    tracker = PerformanceTracker(initial_capital=100000.0)
    
    # Buy 10 shares
    order1 = Order("AAPL", 10, 150.0, OrderStatus.FILLED, filled_quantity=10)
    tracker.record_trade(order1)
    
    assert "AAPL" in tracker.positions
    pos = tracker.positions["AAPL"]
    assert pos.quantity == 10
    assert pos.avg_entry_price == 150.0
    
    # Buy 10 more shares at different price
    order2 = Order("AAPL", 10, 160.0, OrderStatus.FILLED, filled_quantity=10)
    tracker.record_trade(order2)
    
    pos = tracker.positions["AAPL"]
    assert pos.quantity == 20
    assert pos.avg_entry_price == 155.0  # (10*150 + 10*160) / 20
    
    # Sell 15 shares
    order3 = Order("AAPL", -15, 170.0, OrderStatus.FILLED, filled_quantity=15)
    tracker.record_trade(order3)
    
    pos = tracker.positions["AAPL"]
    assert pos.quantity == 5
    assert pos.avg_entry_price == 155.0  # Average doesn't change on sell


def test_position_closing():
    """Test that closing a position records P&L."""
    tracker = PerformanceTracker(initial_capital=100000.0)
    
    # Buy 10 shares at $150
    order1 = Order("AAPL", 10, 150.0, OrderStatus.FILLED, filled_quantity=10)
    tracker.record_trade(order1)
    
    # Sell all 10 shares at $170 (profit)
    order2 = Order("AAPL", -10, 170.0, OrderStatus.FILLED, filled_quantity=10)
    tracker.record_trade(order2)
    
    # Position should be closed
    assert "AAPL" not in tracker.positions
    assert len(tracker.closed_pnls) == 1
    assert tracker.closed_pnls[0] == 200.0  # (170 - 150) * 10


def test_unrealized_pnl():
    """Test unrealized P&L calculation."""
    tracker = PerformanceTracker(initial_capital=100000.0)
    
    # Buy 10 shares at $150
    order1 = Order("AAPL", 10, 150.0, OrderStatus.FILLED, filled_quantity=10)
    tracker.record_trade(order1)
    
    # Update market price to $170
    tracker.update_market_price("AAPL", 170.0)
    
    pos = tracker.positions["AAPL"]
    assert pos.current_price == 170.0
    assert pos.unrealized_pnl == 200.0  # (170 - 150) * 10
    assert pos.unrealized_pnl_pct == pytest.approx(13.33, abs=0.1)


def test_equity_curve():
    """Test equity curve recording."""
    tracker = PerformanceTracker(initial_capital=100000.0)
    
    from trading_lib.portfolio import SimplePortfolio
    
    portfolio = SimplePortfolio(cash=100000.0)
    tracker.record_portfolio_value(portfolio, datetime(2024, 1, 1))
    
    # Make a trade
    order = Order("AAPL", 10, 150.0, OrderStatus.FILLED, filled_quantity=10)
    tracker.record_trade(order)
    portfolio.apply_order(order)
    
    tracker.update_market_price("AAPL", 160.0)
    tracker.record_portfolio_value(portfolio, datetime(2024, 1, 2))
    
    timestamps, values = tracker.get_equity_curve_data()
    assert len(timestamps) == 2
    assert values[0] == 100000.0
    assert values[1] == 100100.0  # 98500 cash + 10*160 holdings = 98500 + 1600


def test_performance_metrics():
    """Test performance metrics calculation."""
    tracker = PerformanceTracker(initial_capital=100000.0)
    
    # Buy and sell for profit
    order1 = Order("AAPL", 10, 150.0, OrderStatus.FILLED, filled_quantity=10)
    tracker.record_trade(order1)
    
    order2 = Order("AAPL", -10, 170.0, OrderStatus.FILLED, filled_quantity=10)
    tracker.record_trade(order2)
    
    # Record portfolio values
    from trading_lib.portfolio import SimplePortfolio
    portfolio = SimplePortfolio(cash=100000.0)
    
    portfolio.apply_order(order1)
    tracker.record_portfolio_value(portfolio, datetime(2024, 1, 1))
    
    portfolio.apply_order(order2)
    tracker.record_portfolio_value(portfolio, datetime(2024, 1, 2))
    
    metrics = tracker.calculate_metrics()
    
    assert metrics.total_trades == 2
    assert metrics.winning_trades == 1
    assert metrics.losing_trades == 0
    assert metrics.total_pnl == 200.0
    assert metrics.win_rate == 100.0
    assert metrics.initial_capital == 100000.0


def test_drawdown_calculation():
    """Test maximum drawdown calculation."""
    tracker = PerformanceTracker(initial_capital=100000.0)
    
    from trading_lib.portfolio import SimplePortfolio
    portfolio = SimplePortfolio(cash=100000.0)
    
    # Record equity curve with drawdown
    tracker.record_portfolio_value(portfolio, datetime(2024, 1, 1))  # 100k
    portfolio.cash = 110000.0
    tracker.record_portfolio_value(portfolio, datetime(2024, 1, 2))  # 110k (peak)
    portfolio.cash = 95000.0
    tracker.record_portfolio_value(portfolio, datetime(2024, 1, 3))  # 95k (drawdown)
    portfolio.cash = 105000.0
    tracker.record_portfolio_value(portfolio, datetime(2024, 1, 4))  # 105k
    
    max_dd, max_dd_pct = tracker._calculate_drawdown()
    assert max_dd == 15000.0  # 110k - 95k
    assert max_dd_pct == pytest.approx(13.64, abs=0.1)  # 15k / 110k * 100


def test_multiple_symbols():
    """Test tracking multiple symbols."""
    tracker = PerformanceTracker(initial_capital=100000.0)
    
    order1 = Order("AAPL", 10, 150.0, OrderStatus.FILLED, filled_quantity=10)
    order2 = Order("MSFT", 5, 200.0, OrderStatus.FILLED, filled_quantity=5)
    
    tracker.record_trade(order1)
    tracker.record_trade(order2)
    
    assert len(tracker.positions) == 2
    assert "AAPL" in tracker.positions
    assert "MSFT" in tracker.positions


def test_reset():
    """Test resetting the tracker."""
    tracker = PerformanceTracker(initial_capital=100000.0)
    
    order = Order("AAPL", 10, 150.0, OrderStatus.FILLED, filled_quantity=10)
    tracker.record_trade(order)
    tracker.update_market_price("AAPL", 160.0)
    
    assert len(tracker.trades) == 1
    assert len(tracker.positions) == 1
    
    tracker.reset()
    
    assert len(tracker.trades) == 0
    assert len(tracker.positions) == 0
    assert len(tracker.equity_curve) == 0
    assert tracker.current_capital == 100000.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

