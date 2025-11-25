import pytest
from unittest.mock import Mock, MagicMock

from trading_lib.engine import TradingEngine
from trading_lib.portfolio import SimplePortfolio
from trading_lib.order_manager import OrderManager
from trading_lib.models import Order, OrderStatus, MarketDataPoint
from trading_lib.strategies import Strategy
from datetime import datetime


class MockStrategy(Strategy):
    """Mock strategy that doesn't generate signals."""
    def generate_signals(self, tick: MarketDataPoint):
        return []


class MockGateway:
    """Mock gateway for testing."""
    def __init__(self):
        self._market_data_callbacks = []
        self._order_update_callbacks = []
    
    def subscribe_market_data(self, callback):
        self._market_data_callbacks.append(callback)
    
    def subscribe_order_updates(self, callback):
        self._order_update_callbacks.append(callback)
    
    def submit_order(self, order):
        # Simulate order submission - set to ACTIVE
        order.status = OrderStatus.ACTIVE
        self._publish_order_update(order)
    
    def _publish_order_update(self, order):
        for callback in self._order_update_callbacks:
            callback(order)
    
    def run(self):
        pass  # Mock doesn't actually run


def test_partial_fill_flow():
    """Test the complete flow of a partial fill."""
    portfolio = SimplePortfolio(cash=10000)
    order_manager = OrderManager(portfolio=portfolio)
    gateway = MockGateway()
    strategy = MockStrategy()
    
    engine = TradingEngine(
        gateway=gateway,
        strategy=strategy,
        portfolio=portfolio,
        order_manager=order_manager
    )
    
    # Create an order
    order = Order("AAPL", 100, 100.0, OrderStatus.ACTIVE, filled_quantity=0)
    
    # Record order in manager
    order_manager.record_order(order)
    assert len(order_manager.get_active_orders()) == 1
    
    # Simulate first partial fill: 30 shares
    order.filled_quantity = 30
    order.status = OrderStatus.PARTIALLY_FILLED
    gateway._publish_order_update(order)
    
    # Check that portfolio was updated with 30 shares
    assert portfolio.get_holding("AAPL")["quantity"] == 30
    assert portfolio.cash == 7000  # 10000 - (30 * 100)
    
    # Order should still be active
    assert len(order_manager.get_active_orders()) == 1
    assert order.status == OrderStatus.PARTIALLY_FILLED
    
    # Simulate second partial fill: 50 more shares (total 80)
    order.filled_quantity = 80
    gateway._publish_order_update(order)
    
    # Check portfolio updated with additional 50 shares
    assert portfolio.get_holding("AAPL")["quantity"] == 80
    assert portfolio.cash == 2000  # 10000 - (80 * 100)
    
    # Order still active
    assert len(order_manager.get_active_orders()) == 1
    
    # Final fill: remaining 20 shares
    order.filled_quantity = 100
    order.status = OrderStatus.FILLED
    gateway._publish_order_update(order)
    
    # Check final state
    assert portfolio.get_holding("AAPL")["quantity"] == 100
    assert portfolio.cash == 0  # 10000 - (100 * 100)
    
    # Order should be removed from active orders
    assert len(order_manager.get_active_orders()) == 0
    assert order.status == OrderStatus.FILLED


def test_full_fill_immediately():
    """Test order that fills completely immediately."""
    portfolio = SimplePortfolio(cash=10000)
    order_manager = OrderManager(portfolio=portfolio)
    gateway = MockGateway()
    strategy = MockStrategy()
    
    engine = TradingEngine(
        gateway=gateway,
        strategy=strategy,
        portfolio=portfolio,
        order_manager=order_manager
    )
    
    order = Order("AAPL", 50, 100.0, OrderStatus.ACTIVE, filled_quantity=0)
    order_manager.record_order(order)
    
    # Full fill immediately
    order.filled_quantity = 50
    order.status = OrderStatus.FILLED
    gateway._publish_order_update(order)
    
    assert portfolio.get_holding("AAPL")["quantity"] == 50
    assert portfolio.cash == 5000
    assert len(order_manager.get_active_orders()) == 0


def test_multiple_orders_partial_fills():
    """Test multiple orders with partial fills."""
    portfolio = SimplePortfolio(cash=20000)
    order_manager = OrderManager(portfolio=portfolio)
    gateway = MockGateway()
    strategy = MockStrategy()
    
    engine = TradingEngine(
        gateway=gateway,
        strategy=strategy,
        portfolio=portfolio,
        order_manager=order_manager
    )
    
    # Two orders
    order1 = Order("AAPL", 50, 100.0, OrderStatus.ACTIVE, filled_quantity=0)
    order2 = Order("MSFT", 30, 200.0, OrderStatus.ACTIVE, filled_quantity=0)
    
    order_manager.record_order(order1)
    order_manager.record_order(order2)
    
    # Partially fill order1
    order1.filled_quantity = 25
    order1.status = OrderStatus.PARTIALLY_FILLED
    gateway._publish_order_update(order1)
    
    assert portfolio.get_holding("AAPL")["quantity"] == 25
    assert len(order_manager.get_active_orders()) == 2
    
    # Fully fill order2
    order2.filled_quantity = 30
    order2.status = OrderStatus.FILLED
    gateway._publish_order_update(order2)
    
    assert portfolio.get_holding("MSFT")["quantity"] == 30
    assert len(order_manager.get_active_orders()) == 1  # order1 still active
    
    # Complete order1
    order1.filled_quantity = 50
    order1.status = OrderStatus.FILLED
    gateway._publish_order_update(order1)
    
    assert portfolio.get_holding("AAPL")["quantity"] == 50
    assert len(order_manager.get_active_orders()) == 0


def test_order_cancellation():
    """Test that canceled orders are removed from tracking."""
    portfolio = SimplePortfolio(cash=10000)
    order_manager = OrderManager(portfolio=portfolio)
    gateway = MockGateway()
    strategy = MockStrategy()
    
    engine = TradingEngine(
        gateway=gateway,
        strategy=strategy,
        portfolio=portfolio,
        order_manager=order_manager
    )
    
    order = Order("AAPL", 100, 100.0, OrderStatus.ACTIVE, filled_quantity=0)
    order_manager.record_order(order)
    
    # Partially fill
    order.filled_quantity = 30
    order.status = OrderStatus.PARTIALLY_FILLED
    gateway._publish_order_update(order)
    
    assert len(order_manager.get_active_orders()) == 1
    
    # Cancel order
    order.status = OrderStatus.CANCELED
    gateway._publish_order_update(order)
    
    assert len(order_manager.get_active_orders()) == 0
    # Portfolio should only have the 30 shares that were filled
    assert portfolio.get_holding("AAPL")["quantity"] == 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

