"""Order Manager for validation and risk checks before submission."""

from datetime import datetime, timedelta
from collections import deque
from typing import Optional

from trading_lib.models import Order
from trading_lib.portfolio import Portfolio


class OrderManager:
    """Validates orders and enforces risk limits before submission.
    
    Risk Controls:
    - Capital sufficiency (via Portfolio)
    - Orders per minute throttling
    - Position limits (max buy/sell exposure)
    """
    
    def __init__(
        self,
        portfolio: Portfolio,
        max_orders_per_minute: int = 60,
        max_position_size: Optional[float] = None,
        max_order_value: Optional[float] = None
    ):
        """Initialize Order Manager.
        
        Args:
            portfolio: Portfolio for capital checks
            max_orders_per_minute: Rate limit for order submission
            max_position_size: Max total position value (buy + sell)
            max_order_value: Max value per individual order
        """
        self.portfolio = portfolio
        self.max_orders_per_minute = max_orders_per_minute
        self.max_position_size = max_position_size
        self.max_order_value = max_order_value
        
        # Order rate tracking
        self._order_timestamps = deque(maxlen=max_orders_per_minute)
        
        # Position tracking
        self._position_values = {}  # {symbol: net_position_value}
    
    def validate_order(self, order: Order) -> tuple[bool, str]:
        """Validate order against all risk checks.
        
        Args:
            order: Order to validate
        
        Returns:
            (is_valid, reason) tuple
        """
        # Check 1: Capital sufficiency
        if not self.portfolio.can_execute_order(order):
            if order.quantity > 0:
                return False, "Insufficient cash"
            else:
                return False, "Insufficient holdings"
        
        # Check 2: Orders per minute limit
        if not self._check_rate_limit():
            return False, f"Rate limit exceeded ({self.max_orders_per_minute} orders/min)"
        
        # Check 3: Individual order value limit
        if self.max_order_value:
            order_value = abs(order.quantity * order.price)
            if order_value > self.max_order_value:
                return False, f"Order value ${order_value:.2f} exceeds limit ${self.max_order_value:.2f}"
        
        # Check 4: Position size limit
        if self.max_position_size:
            if not self._check_position_limit(order):
                return False, f"Position limit exceeded (max ${self.max_position_size:.2f})"
        
        return True, "Valid"
    
    def _check_rate_limit(self) -> bool:
        """Check if order rate is within limits."""
        now = datetime.now()
        
        # Remove timestamps older than 1 minute
        cutoff = now - timedelta(minutes=1)
        while self._order_timestamps and self._order_timestamps[0] < cutoff:
            self._order_timestamps.popleft()
        
        # Check if under limit
        return len(self._order_timestamps) < self.max_orders_per_minute
    
    def _check_position_limit(self, order: Order) -> bool:
        """Check if order would exceed position limits."""
        symbol = order.symbol
        
        # Get current position value
        current_position = self._position_values.get(symbol, 0.0)
        
        # Calculate new position if order executes
        order_value = order.quantity * order.price  # Positive for buy, negative for sell
        new_position = abs(current_position + order_value)
        
        return new_position <= self.max_position_size
    
    def record_order(self, order: Order):
        """Record order submission for rate limiting and position tracking.
        
        Call this AFTER order is submitted to Gateway.
        """
        # Record timestamp for rate limiting
        self._order_timestamps.append(datetime.now())
        
        # Update position tracking
        symbol = order.symbol
        order_value = order.quantity * order.price
        self._position_values[symbol] = self._position_values.get(symbol, 0.0) + order_value
    
    def get_order_rate(self) -> int:
        """Get current orders per minute rate."""
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)
        
        # Count orders in last minute
        count = sum(1 for ts in self._order_timestamps if ts >= cutoff)
        return count
    
    def get_position_value(self, symbol: str) -> float:
        """Get current position value for a symbol."""
        return self._position_values.get(symbol, 0.0)
    
    def get_all_positions(self) -> dict:
        """Get all position values."""
        return self._position_values.copy()
    
    def reset_positions(self):
        """Reset position tracking (e.g., end of day)."""
        self._position_values.clear()


if __name__ == "__main__":
    from trading_lib.portfolio import SimplePortfolio
    from trading_lib.models import OrderStatus
    
    print("="*60)
    print("Order Manager Validation Examples")
    print("="*60)
    
    # Create portfolio and order manager
    portfolio = SimplePortfolio(cash=10000, holdings={})
    om = OrderManager(
        portfolio=portfolio,
        max_orders_per_minute=5,
        max_position_size=20000,
        max_order_value=5000
    )
    
    # Test 1: Valid order
    order1 = Order("AAPL", 10, 100.0, OrderStatus.PENDING)
    valid, reason = om.validate_order(order1)
    print(f"\nOrder 1: 10 @ $100")
    print(f"  Valid: {valid}, Reason: {reason}")
    if valid:
        om.record_order(order1)
    
    # Test 2: Order exceeding value limit
    order2 = Order("AAPL", 100, 100.0, OrderStatus.PENDING)
    valid, reason = om.validate_order(order2)
    print(f"\nOrder 2: 100 @ $100 (value $10,000)")
    print(f"  Valid: {valid}, Reason: {reason}")
    
    # Test 3: Rate limit test
    print(f"\nSubmitting multiple orders to test rate limit...")
    for i in range(6):
        order = Order("AAPL", 1, 100.0, OrderStatus.PENDING)
        valid, reason = om.validate_order(order)
        if valid:
            om.record_order(order)
            print(f"  Order {i+1}: Accepted (rate: {om.get_order_rate()}/min)")
        else:
            print(f"  Order {i+1}: Rejected - {reason}")
    
    print("\n" + "="*60)

