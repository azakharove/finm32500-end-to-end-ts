"""Example: Run backtest using config file.

This is the same as running: python main.py --config config_simulation.json
But shows how to do it programmatically.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_lib.config import load_config
from trading_lib import create_gateway
from trading_lib.engine import TradingEngine
from trading_lib.strategies.factory import create_strategy
from trading_lib.portfolio import SimplePortfolio
from trading_lib.order_manager import OrderManager
from trading_lib.performance import PerformanceTracker


def main():
    """Run a backtest using config file."""
    
    # Load config (same as main.py)
    config = load_config("config_simulation.json")
    
    # Create gateway
    gateway = create_gateway(config.gateway)
    
    # Create strategy from config
    strategy = create_strategy(config.strategy)
    
    # Create portfolio
    portfolio = SimplePortfolio(cash=config.initial_capital)
    
    # Create order manager
    order_manager = OrderManager(
        portfolio=portfolio,
        max_orders_per_minute=config.max_orders_per_minute,
        max_order_value=config.max_order_value
    )
    
    # Create performance tracker
    performance_tracker = PerformanceTracker(initial_capital=config.initial_capital)
    
    # Create and run engine
    engine = TradingEngine(
        gateway=gateway,
        strategy=strategy,
        portfolio=portfolio,
        order_manager=order_manager,
        performance_tracker=performance_tracker
    )
    
    print("Running backtest...")
    try:
        engine.run()
    finally:
        gateway.disconnect()
    
    # Calculate metrics
    metrics = performance_tracker.calculate_metrics()
    
    print(f"\nBacktest complete!")
    print(f"Total Return: ${metrics.total_return:,.2f} ({metrics.total_return_pct:.2f}%)")
    print(f"Total Trades: {metrics.total_trades}")
    print(f"\nNote: Use 'python main.py --config config_simulation.json' for automatic report generation")


if __name__ == "__main__":
    main()

