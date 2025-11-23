from trading_lib.models import MarketDataPoint, OrderStatus, Order, Action
from trading_lib.gateway import Gateway
from trading_lib.strategies import Strategy
from trading_lib.portfolio import Portfolio
from trading_lib.order_manager import OrderManager
from trading_lib.logging_config import get_logger

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
    
    def __init__(self, gateway: Gateway, strategy: Strategy, portfolio: Portfolio, order_manager: OrderManager):
        self.gateway = gateway
        self.strategy = strategy
        self.portfolio = portfolio
        self.order_manager = order_manager
        self.logger = get_logger('engine')
        
        self._setup_subscriptions()
    
    def _setup_subscriptions(self):
        # Subscribe to market data
        self.gateway.subscribe_market_data(self._on_market_data)
        
        # Subscribe to order updates
        self.gateway.subscribe_order_updates(self._on_order_update)
    
    def _on_market_data(self, tick: MarketDataPoint):
        signals = self.strategy.generate_signals(tick)
        
        for signal in signals:
            symbol, quantity, price, action = signal
            if action == Action.HOLD:
                continue
                
            order = Order(symbol=symbol, quantity=quantity, price=price, status=OrderStatus.PENDING)
            
            if self.order_manager.validate_order(order):
                self.gateway.submit_order(order)
            else:
                self.logger.warning(f"Order validation failed: {order.symbol} {order.quantity}@{order.price}")
    
    def _on_order_update(self, order: Order):
        if order.status == OrderStatus.COMPLETED:
            self.portfolio.apply_order(order)
            self.order_manager.record_order(order)
            self.logger.info(f"Order filled: {order.symbol} {order.quantity}@{order.price}")
        elif order.status == OrderStatus.FAILED:
            self.order_manager.record_order(order)
            self.logger.warning(f"Order failed: {order.symbol} {order.quantity}@{order.price}")
    
    def run(self):
        """Start the trading engine."""
        self.gateway.run()        
