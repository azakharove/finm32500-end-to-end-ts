import pytest

from trading_lib.exceptions import ExecutionError, OrderError
from trading_lib.models import Order, OrderStatus


def test_order_error_with_order():
    """Test OrderError with an order object."""
    order = Order("AAPL", 10, 150.0, OrderStatus.PENDING)
    error = OrderError(order, "Test error message")
    
    assert "Test error message" in str(error)
    assert "AAPL" in str(error)


def test_order_error_without_order():
    """Test OrderError with just a reason."""
    error = OrderError(reason="Insufficient holdings")
    
    assert "Insufficient holdings" in str(error)


def test_execution_error():
    """Test ExecutionError."""
    order = Order("MSFT", 5, 200.0, OrderStatus.PENDING)
    error = ExecutionError(order, "Execution failed")
    
    assert "Execution failed" in str(error)
    assert "MSFT" in str(error)

