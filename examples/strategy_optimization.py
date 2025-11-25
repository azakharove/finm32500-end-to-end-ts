"""Example: Iteratively test different strategy configurations.

This uses the same infrastructure as main.py - just creates the components
directly for programmatic testing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_lib import create_gateway, load_config
from trading_lib.engine import TradingEngine
from trading_lib.strategies.factory import create_strategy
from trading_lib.portfolio import SimplePortfolio
from trading_lib.order_manager import OrderManager
from trading_lib.performance import PerformanceTracker, PerformanceMetrics
from trading_lib.config import GatewayConfig, Mode


def test_strategy_config(config: dict, csv_path: str = "AAPL_5d_1m.csv") -> PerformanceMetrics:
    """Test a strategy configuration using the same infrastructure as main.py."""
    initial_capital = 100000.0
    
    # Create gateway (simulation mode)
    gateway_config = GatewayConfig(
        mode=Mode.SIMULATION,
        csv_path=csv_path,
        data_dir="data"
    )
    gateway = create_gateway(gateway_config)
    
    # Create strategy
    strategy = create_strategy(config)
    
    # Create portfolio
    portfolio = SimplePortfolio(cash=initial_capital)
    
    # Create order manager
    order_manager = OrderManager(
        portfolio=portfolio,
        max_orders_per_minute=60,
        max_order_value=50000.0
    )
    
    # Create performance tracker
    performance_tracker = PerformanceTracker(initial_capital=initial_capital)
    
    # Create and run engine
    engine = TradingEngine(
        gateway=gateway,
        strategy=strategy,
        portfolio=portfolio,
        order_manager=order_manager,
        performance_tracker=performance_tracker
    )
    
    try:
        engine.run()
    finally:
        gateway.disconnect()
    
    # Calculate and return metrics
    return performance_tracker.calculate_metrics()


def main():
    """Test different strategy configurations."""
    print("Strategy Optimization - Testing Different Configurations")
    print("="*70)
    
    # Test different RSI configurations
    configs = [
        {
            "name": "RSI Default",
            "config": {"type": "rsi", "period": 14, "oversold": 30, "overbought": 70, "quantity": 10}
        },
        {
            "name": "RSI Wide Bands",
            "config": {"type": "rsi", "period": 14, "oversold": 25, "overbought": 75, "quantity": 10}
        },
        {
            "name": "RSI Tight Bands",
            "config": {"type": "rsi", "period": 14, "oversold": 35, "overbought": 65, "quantity": 10}
        },
        {
            "name": "RSI Long Period",
            "config": {"type": "rsi", "period": 21, "oversold": 30, "overbought": 70, "quantity": 10}
        },
        {
            "name": "Moving Average",
            "config": {"type": "moving_average", "short_window": 5, "long_window": 20, "quantity": 10}
        },
    ]
    
    results = []
    for item in configs:
        print(f"\nTesting: {item['name']}...")
        metrics = test_strategy_config(item['config'])
        results.append((item['name'], metrics))
        print(f"  Return: ${metrics.total_return:,.2f} ({metrics.total_return_pct:.2f}%) | "
              f"Trades: {metrics.total_trades} | Sharpe: {metrics.sharpe_ratio:.2f}")
    
    # Sort by total return
    results.sort(key=lambda x: x[1].total_return, reverse=True)
    
    print(f"\n{'='*70}")
    print("RESULTS SUMMARY (sorted by return)")
    print(f"{'='*70}")
    print(f"{'Strategy':<25} {'Return %':<12} {'Trades':<8} {'Win Rate':<10} {'Sharpe':<8} {'Max DD %':<10}")
    print("-" * 85)
    for name, m in results:
        print(f"{name:<25} {m.total_return_pct:>10.2f}%  {m.total_trades:>6}  {m.win_rate:>8.2f}%  "
              f"{m.sharpe_ratio:>6.2f}  {m.max_drawdown_pct:>8.2f}%")
    
    best = results[0]
    print(f"\n✓ Best strategy: {best[0]}")
    print(f"  Return: ${best[1].total_return:,.2f} ({best[1].total_return_pct:.2f}%)")
    print(f"  Sharpe: {best[1].sharpe_ratio:.2f}")
    print(f"  Max Drawdown: {best[1].max_drawdown_pct:.2f}%")


if __name__ == "__main__":
    main()

