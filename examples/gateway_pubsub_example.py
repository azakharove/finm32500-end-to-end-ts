"""Example: Using Gateway with publish-subscribe pattern."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_lib.gateway import SimulationGateway
from trading_lib.models import MarketDataPoint, Order, OrderStatus, Action
from trading_lib.portfolio import SimplePortfolio
from trading_lib.strategies import MovingAverageStrategy


class TradingSystem:
    """Simple trading system that uses Gateway pattern."""
    
    def __init__(self, gateway, strategy, portfolio):
        self.gateway = gateway
        self.strategy = strategy
        self.portfolio = portfolio
        self.tick_count = 0
        
        # Subscribe to market data
        self.gateway.subscribe_market_data(self.on_market_data)
        
        # Subscribe to order updates
        self.gateway.subscribe_order_updates(self.on_order_update)
    
    def on_market_data(self, data_point: MarketDataPoint):
        """Called when new market data arrives."""
        self.tick_count += 1
        
        # Show progress
        if self.tick_count % 100 == 0:
            print(f"Processed {self.tick_count} ticks...")
        
        # Generate trading signals
        signals = self.strategy.generate_signals(data_point)
        
        # Process signals and submit orders
        for symbol, quantity, price, action in signals:
            if action != Action.HOLD:
                # Check if we can execute
                order = Order(symbol, quantity, price, OrderStatus.PENDING)
                
                if self.portfolio.can_execute_order(order):
                    print(f"Submitting order: {symbol} {quantity}@{price}")
                    self.gateway.submit_order(order)
                else:
                    print(f"Cannot execute order: Insufficient funds/holdings")
    
    def on_order_update(self, order: Order):
        """Called when order status changes."""
        if order.status == OrderStatus.COMPLETED:
            print(f"Order filled: {order.symbol} {order.quantity}@{order.price}")
            # Update portfolio
            self.portfolio.apply_order(order)
        elif order.status == OrderStatus.FAILED:
            print(f"Order failed: {order.symbol}")
    
    def run(self):
        """Start the trading system."""
        print("Starting trading system...")
        print("=" * 60)
        
        # This will block and process all data
        self.gateway.run()
        
        # Show final results
        self.show_results()
    
    def show_results(self):
        """Display trading results."""
        print("\n" + "=" * 60)
        print("TRADING RESULTS")
        print("=" * 60)
        print(f"Total ticks processed: {self.tick_count}")
        print(f"Final cash: ${self.portfolio.get_cash():.2f}")
        print(f"Holdings: {self.portfolio.get_all_holdings()}")


def main():
    """Run the example."""
    print("=" * 60)
    print("GATEWAY PUB/SUB PATTERN EXAMPLE")
    print("=" * 60)
    print()
    
    # Create gateway (simulation mode)
    gateway = SimulationGateway(csv_path='AAPL_5d_1m.csv', data_dir='data')
    gateway.connect()
    
    # Create strategy and portfolio
    strategy = MovingAverageStrategy(short_window=20, long_window=50, quantity=10)
    portfolio = SimplePortfolio(cash=10000, holdings={})
    
    # Create trading system
    system = TradingSystem(gateway, strategy, portfolio)
    
    # Run!
    try:
        system.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        gateway.disconnect()


if __name__ == "__main__":
    main()

