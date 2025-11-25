from trading_lib.models import MarketDataPoint, OrderStatus, Order, Action
from trading_lib.gateway import Gateway
from trading_lib.strategies import Strategy
from trading_lib.portfolio import Portfolio
from trading_lib.order_manager import OrderManager
from trading_lib.logging_config import get_logger
from trading_lib.performance import PerformanceTracker
from typing import Optional
from datetime import datetime

class TradingEngine:
    """Main orchestrator for backtesting and live trading.
    
    Event Flow:
    1. Gateway publishes market data
    2. Strategy subscribes, generates signals -> creates Orders
    3. OrderManager validates Orders
    4. Valid orders -> Gateway.submit_order()
    5. [Sim] MatchingEngine simulates fills using OrderBook
    6. [Live] Real exchange handles fills
    7. Gateway publishes fills -> Portfolio subscribes to fills, updates positions
    """
    
    def __init__(
        self, 
        gateway: Gateway, 
        strategy: Strategy, 
        portfolio: Portfolio, 
        order_manager: OrderManager,
        performance_tracker: Optional[PerformanceTracker] = None
    ):
        self.gateway = gateway
        self.strategy = strategy
        self.portfolio = portfolio
        self.order_manager = order_manager
        self.performance_tracker = performance_tracker
        self.logger = get_logger('engine')
        
        self._setup_subscriptions()
    
    def _setup_subscriptions(self):
        # Subscribe to market data
        self.gateway.subscribe_market_data(self._on_market_data)
        
        # Subscribe to order updates
        self.gateway.subscribe_order_updates(self._on_order_update)
    
    def _on_market_data(self, tick: MarketDataPoint):
        # Update performance tracker with current market price
        if self.performance_tracker:
            self.performance_tracker.update_market_price(tick.symbol, tick.price)
            # Record portfolio value periodically
            self.performance_tracker.record_portfolio_value(self.portfolio, tick.timestamp)
        
        signals = self.strategy.generate_signals(tick)
        
        for signal in signals:
            symbol, quantity, price, action = signal
            if action == Action.HOLD:
                continue
                
            order = Order(symbol=symbol, quantity=quantity, price=price, status=OrderStatus.PENDING, filled_quantity=0)
            
            if self.order_manager.validate_order(order):
                self.gateway.submit_order(order)
            else:
                self.logger.warning(f"Order validation failed: {order.symbol} {order.quantity}@{order.price}")
    
    def _on_order_update(self, order: Order):
        if order.status == OrderStatus.ACTIVE:
            # Order is now active on exchange (acknowledged)
            self.order_manager.record_order(order)
            
            # Check if there's a fill update even though status is ACTIVE
            # (Gateway might send ACTIVE status with filled_quantity > 0)
            if order.filled_quantity > 0:
                new_fill_qty, remaining_qty = self.order_manager.update_order_fill(order, order.filled_quantity)
                if new_fill_qty > 0:
                    self._apply_fill(order, new_fill_qty, datetime.now())
                    # Status is already updated by update_order_fill
                    if remaining_qty > 0:
                        self.logger.info(f"Order partially filled: {order.symbol} {new_fill_qty} filled, {remaining_qty} remaining @{order.price}")
                    else:
                        self.logger.info(f"Order fully filled: {order.symbol} {order.quantity}@{order.price}")
                        self.order_manager.remove_order(order)
            else:
                self.logger.debug(f"Order active: {order.symbol} {order.quantity}@{order.price}")
            
        elif order.status == OrderStatus.PARTIALLY_FILLED:
            # Order partially filled - update tracking and apply fill
            new_fill_qty, remaining_qty = self.order_manager.update_order_fill(order, order.filled_quantity)
            
            if new_fill_qty > 0:
                self._apply_fill(order, new_fill_qty, datetime.now())
                self.logger.info(f"Order partially filled: {order.symbol} {new_fill_qty} filled, {remaining_qty} remaining @{order.price}")
            
        elif order.status == OrderStatus.FILLED:
            # Order fully filled
            new_fill_qty, remaining_qty = self.order_manager.update_order_fill(order, order.filled_quantity)
            
            if new_fill_qty > 0:
                self._apply_fill(order, new_fill_qty, datetime.now())
            
            self.order_manager.record_order(order)
            self.logger.info(f"Order fully filled: {order.symbol} {order.quantity}@{order.price}")
            self.order_manager.remove_order(order)
            
        elif order.status == OrderStatus.FAILED:
            # Order failed to submit
            self.order_manager.record_order(order)
            self.logger.warning(f"Order failed: {order.symbol} {order.quantity}@{order.price}")
            self.order_manager.remove_order(order)
            
        elif order.status == OrderStatus.CANCELED:
            # Order was canceled
            self.order_manager.record_order(order)
            self.logger.info(f"Order canceled: {order.symbol} {order.quantity}@{order.price}")
            self.order_manager.remove_order(order)
    
    def _apply_fill(self, order: Order, fill_quantity: int, timestamp: Optional[datetime] = None):
        """Apply a fill (partial or full) to the portfolio.
        
        Args:
            order: The order being filled
            fill_quantity: The quantity that was just filled (positive number)
            timestamp: Timestamp of the fill (default: now)
        """
        # Create a temporary order with just the fill quantity
        # Use the same sign as original order (buy vs sell)
        fill_sign = 1 if order.quantity > 0 else -1
        fill_order = Order(
            symbol=order.symbol,
            quantity=fill_sign * fill_quantity,
            price=order.price,
            status=OrderStatus.FILLED,
            filled_quantity=fill_quantity
        )
        
        try:
            self.portfolio.apply_order(fill_order)
            
            # Record trade in performance tracker
            if self.performance_tracker:
                self.performance_tracker.record_trade(fill_order, timestamp)
        except ValueError as e:
            # Handle insufficient cash/holdings gracefully
            self.logger.error(f"Failed to apply fill: {e}. Order: {fill_order.symbol} {fill_order.quantity}@{fill_order.price}")
            # Don't record the trade if it couldn't be applied
    
    def run(self):
        """Start the trading engine."""
        self.gateway.run()        
