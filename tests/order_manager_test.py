import pytest
from datetime import datetime, timedelta

from trading_lib.order_manager import OrderManager
from trading_lib.portfolio import SimplePortfolio
from trading_lib.models import Order, OrderStatus


def test_order_tracking():
    """Test that orders are tracked when recorded."""
    portfolio = SimplePortfolio(cash=10000)
    om = OrderManager(portfolio=portfolio)
    
    order = Order("AAPL", 10, 100.0, OrderStatus.PENDING, filled_quantity=0)
    om.record_order(order)
    
    active_orders = om.get_active_orders()
    assert len(active_orders) == 1
    assert id(order) in active_orders


def test_partial_fill_tracking():
    """Test that partial fills are tracked correctly."""
    portfolio = SimplePortfolio(cash=10000)
    om = OrderManager(portfolio=portfolio)
    
    order = Order("AAPL", 100, 100.0, OrderStatus.ACTIVE, filled_quantity=0)
    om.record_order(order)
    
    # First partial fill: 30 shares
    new_fill_qty, remaining_qty = om.update_order_fill(order, filled_quantity=30)
    assert new_fill_qty == 30
    assert remaining_qty == 70
    assert order.filled_quantity == 30
    assert order.status == OrderStatus.PARTIALLY_FILLED
    assert order.remaining_quantity == 70
    
    # Second partial fill: 50 more shares (total 80)
    new_fill_qty, remaining_qty = om.update_order_fill(order, filled_quantity=80)
    assert new_fill_qty == 50  # Only the new fill amount
    assert remaining_qty == 20
    assert order.filled_quantity == 80
    assert order.status == OrderStatus.PARTIALLY_FILLED
    assert order.remaining_quantity == 20
    
    # Final fill: remaining 20 shares
    new_fill_qty, remaining_qty = om.update_order_fill(order, filled_quantity=100)
    assert new_fill_qty == 20
    assert remaining_qty == 0
    assert order.filled_quantity == 100
    assert order.status == OrderStatus.FILLED
    assert order.remaining_quantity == 0
    
    # Order should be removed from active orders
    active_orders = om.get_active_orders()
    assert id(order) not in active_orders


def test_full_fill_immediately():
    """Test order that fills completely on first update."""
    portfolio = SimplePortfolio(cash=10000)
    om = OrderManager(portfolio=portfolio)
    
    order = Order("AAPL", 50, 100.0, OrderStatus.ACTIVE, filled_quantity=0)
    om.record_order(order)
    
    # Full fill immediately
    new_fill_qty, remaining_qty = om.update_order_fill(order, filled_quantity=50)
    assert new_fill_qty == 50
    assert remaining_qty == 0
    assert order.filled_quantity == 50
    assert order.status == OrderStatus.FILLED
    
    # Order should be removed
    active_orders = om.get_active_orders()
    assert id(order) not in active_orders


def test_order_removal():
    """Test that orders can be manually removed."""
    portfolio = SimplePortfolio(cash=10000)
    om = OrderManager(portfolio=portfolio)
    
    order1 = Order("AAPL", 10, 100.0, OrderStatus.ACTIVE, filled_quantity=0)
    order2 = Order("MSFT", 20, 200.0, OrderStatus.ACTIVE, filled_quantity=0)
    
    om.record_order(order1)
    om.record_order(order2)
    
    assert len(om.get_active_orders()) == 2
    
    om.remove_order(order1)
    active_orders = om.get_active_orders()
    assert len(active_orders) == 1
    assert id(order2) in active_orders
    assert id(order1) not in active_orders


def test_multiple_orders_same_symbol():
    """Test tracking multiple orders for the same symbol."""
    portfolio = SimplePortfolio(cash=50000)
    om = OrderManager(portfolio=portfolio)
    
    order1 = Order("AAPL", 10, 100.0, OrderStatus.ACTIVE, filled_quantity=0)
    order2 = Order("AAPL", 20, 100.0, OrderStatus.ACTIVE, filled_quantity=0)
    
    om.record_order(order1)
    om.record_order(order2)
    
    assert len(om.get_active_orders()) == 2
    
    # Partially fill first order
    new_fill_qty, remaining_qty = om.update_order_fill(order1, filled_quantity=5)
    assert new_fill_qty == 5
    assert remaining_qty == 5
    assert order1.status == OrderStatus.PARTIALLY_FILLED
    
    # Second order still active
    assert order2.status == OrderStatus.ACTIVE
    assert len(om.get_active_orders()) == 2


def test_sell_order_tracking():
    """Test tracking sell orders (negative quantity)."""
    portfolio = SimplePortfolio(cash=10000)
    portfolio.add_to_holding("AAPL", 100, 100.0)
    om = OrderManager(portfolio=portfolio)
    
    # Sell order (negative quantity)
    order = Order("AAPL", -50, 150.0, OrderStatus.ACTIVE, filled_quantity=0)
    om.record_order(order)
    
    # Partial fill: 30 shares sold
    new_fill_qty, remaining_qty = om.update_order_fill(order, filled_quantity=30)
    assert new_fill_qty == 30
    assert remaining_qty == 20  # 50 - 30
    assert order.filled_quantity == 30
    assert order.status == OrderStatus.PARTIALLY_FILLED
    
    # Remaining quantity should account for negative quantity
    assert order.remaining_quantity == 20


def test_no_fill_update():
    """Test that updating with same filled_quantity doesn't change anything."""
    portfolio = SimplePortfolio(cash=10000)
    om = OrderManager(portfolio=portfolio)
    
    order = Order("AAPL", 100, 100.0, OrderStatus.ACTIVE, filled_quantity=0)
    om.record_order(order)
    
    # First fill
    new_fill_qty, remaining_qty = om.update_order_fill(order, filled_quantity=50)
    assert new_fill_qty == 50
    assert remaining_qty == 50
    
    # Update with same filled_quantity (no new fill)
    new_fill_qty, remaining_qty = om.update_order_fill(order, filled_quantity=50)
    assert new_fill_qty == 0  # No new fill
    assert remaining_qty == 50
    assert order.status == OrderStatus.PARTIALLY_FILLED


def test_order_validation_with_tracking():
    """Test that order validation works with tracking."""
    portfolio = SimplePortfolio(cash=10000)
    om = OrderManager(
        portfolio=portfolio,
        max_order_value=5000,
        max_position_size=10000
    )
    
    # Valid order
    order1 = Order("AAPL", 10, 100.0, OrderStatus.PENDING, filled_quantity=0)
    valid, reason = om.validate_order(order1)
    assert valid is True
    assert reason == "Valid"
    
    # Invalid order (exceeds max value)
    order2 = Order("AAPL", 100, 100.0, OrderStatus.PENDING, filled_quantity=0)
    valid, reason = om.validate_order(order2)
    assert valid is False
    assert "exceeds limit" in reason


def test_rate_limiting():
    """Test that rate limiting works correctly."""
    portfolio = SimplePortfolio(cash=100000)
    om = OrderManager(portfolio=portfolio, max_orders_per_minute=3)
    
    # Submit 3 orders - all should be valid
    for i in range(3):
        order = Order("AAPL", 10, 100.0, OrderStatus.PENDING, filled_quantity=0)
        valid, reason = om.validate_order(order)
        assert valid is True
        om.record_order(order)
    
    # 4th order should be rate limited
    order4 = Order("AAPL", 10, 100.0, OrderStatus.PENDING, filled_quantity=0)
    valid, reason = om.validate_order(order4)
    assert valid is False
    assert "Rate limit" in reason


def test_position_tracking():
    """Test that position values are tracked correctly."""
    portfolio = SimplePortfolio(cash=10000)
    om = OrderManager(portfolio=portfolio, max_position_size=5000)
    
    # First order
    order1 = Order("AAPL", 10, 100.0, OrderStatus.PENDING, filled_quantity=0)
    om.record_order(order1)
    assert om.get_position_value("AAPL") == 1000.0
    
    # Second order for same symbol
    order2 = Order("AAPL", 20, 100.0, OrderStatus.PENDING, filled_quantity=0)
    om.record_order(order2)
    assert om.get_position_value("AAPL") == 3000.0  # 10*100 + 20*100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

