"""Comprehensive strategy optimization - test many configurations to find the best."""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_lib import create_gateway
from trading_lib.engine import TradingEngine
from trading_lib.strategies.factory import create_strategy
from trading_lib.portfolio import SimplePortfolio
from trading_lib.order_manager import OrderManager
from trading_lib.performance import PerformanceTracker, PerformanceMetrics
from trading_lib.config import GatewayConfig, Mode


def test_strategy_config(config: dict, csv_path: str = "AAPL_5d_1m.csv") -> PerformanceMetrics:
    """Test a strategy configuration."""
    initial_capital = 100000.0
    
    gateway_config = GatewayConfig(
        mode=Mode.SIMULATION,
        csv_path=csv_path,
        data_dir="data"
    )
    gateway = create_gateway(gateway_config)
    
    strategy = create_strategy(config)
    portfolio = SimplePortfolio(cash=initial_capital)
    order_manager = OrderManager(
        portfolio=portfolio,
        max_orders_per_minute=60,
        max_order_value=50000.0
    )
    performance_tracker = PerformanceTracker(initial_capital=initial_capital)
    
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
    
    return performance_tracker.calculate_metrics()


def save_results_to_markdown(results: list, best: tuple):
    """Save optimization results to a markdown file."""
    # Create directory
    output_dir = Path("strategy_performance")
    output_dir.mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"strategy_comparison_{timestamp}.md"
    
    with open(report_path, 'w') as f:
        f.write("# Strategy Performance Comparison\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        
        # Best strategy section
        f.write("## 🏆 Best Strategy\n\n")
        f.write(f"**Name:** {best[0]}\n\n")
        f.write(f"**Configuration:**\n```json\n{json.dumps(best[2], indent=2)}\n```\n\n")
        f.write("**Performance Metrics:**\n\n")
        f.write(f"- **Total Return:** ${best[1].total_return:,.2f} ({best[1].total_return_pct:.2f}%)\n")
        f.write(f"- **Total Trades:** {best[1].total_trades}\n")
        f.write(f"- **Win Rate:** {best[1].win_rate:.2f}%\n")
        f.write(f"- **Winning Trades:** {best[1].winning_trades}\n")
        f.write(f"- **Losing Trades:** {best[1].losing_trades}\n")
        f.write(f"- **Average Win:** ${best[1].avg_win:,.2f}\n")
        f.write(f"- **Average Loss:** ${best[1].avg_loss:,.2f}\n")
        f.write(f"- **Profit Factor:** {best[1].profit_factor:.2f}\n")
        f.write(f"- **Sharpe Ratio:** {best[1].sharpe_ratio:.2f}\n")
        f.write(f"- **Max Drawdown:** ${best[1].max_drawdown:,.2f} ({best[1].max_drawdown_pct:.2f}%)\n")
        f.write(f"- **Initial Capital:** ${best[1].initial_capital:,.2f}\n")
        f.write(f"- **Final Capital:** ${best[1].final_capital:,.2f}\n\n")
        
        f.write("---\n\n")
        
        # All results table
        f.write("## All Strategies (Sorted by Return)\n\n")
        f.write("| Rank | Strategy | Return % | Trades | Win % | Sharpe | Max DD % | Initial Capital | Final Capital |\n")
        f.write("|------|----------|----------|--------|-------|--------|----------|-----------------|---------------|\n")
        
        for rank, (name, m, config) in enumerate(results, 1):
            f.write(f"| {rank} | {name} | {m.total_return_pct:.2f}% | {m.total_trades} | "
                   f"{m.win_rate:.1f}% | {m.sharpe_ratio:.2f} | {m.max_drawdown_pct:.2f}% | "
                   f"${m.initial_capital:,.2f} | ${m.final_capital:,.2f} |\n")
        
        f.write("\n---\n\n")
        
        # Detailed metrics for top 10
        f.write("## Top 10 Strategies - Detailed Metrics\n\n")
        for rank, (name, m, config) in enumerate(results[:10], 1):
            f.write(f"### {rank}. {name}\n\n")
            f.write(f"**Configuration:**\n```json\n{json.dumps(config, indent=2)}\n```\n\n")
            f.write("**Metrics:**\n\n")
            f.write(f"- Return: ${m.total_return:,.2f} ({m.total_return_pct:.2f}%)\n")
            f.write(f"- Total Trades: {m.total_trades}\n")
            f.write(f"- Win Rate: {m.win_rate:.2f}% ({m.winning_trades} wins, {m.losing_trades} losses)\n")
            f.write(f"- Average Win: ${m.avg_win:,.2f}\n")
            f.write(f"- Average Loss: ${m.avg_loss:,.2f}\n")
            f.write(f"- Profit Factor: {m.profit_factor:.2f}\n")
            f.write(f"- Sharpe Ratio: {m.sharpe_ratio:.2f}\n")
            f.write(f"- Max Drawdown: ${m.max_drawdown:,.2f} ({m.max_drawdown_pct:.2f}%)\n")
            f.write(f"- Initial Capital: ${m.initial_capital:,.2f}\n")
            f.write(f"- Final Capital: ${m.final_capital:,.2f}\n\n")
        
        # Summary statistics
        f.write("---\n\n")
        f.write("## Summary Statistics\n\n")
        returns = [r[1].total_return_pct for r in results]
        sharpe_ratios = [r[1].sharpe_ratio for r in results]
        win_rates = [r[1].win_rate for r in results]
        
        f.write(f"- **Total Strategies Tested:** {len(results)}\n")
        f.write(f"- **Average Return:** {sum(returns) / len(returns):.2f}%\n")
        f.write(f"- **Best Return:** {max(returns):.2f}%\n")
        f.write(f"- **Worst Return:** {min(returns):.2f}%\n")
        f.write(f"- **Average Sharpe Ratio:** {sum(sharpe_ratios) / len(sharpe_ratios):.2f}\n")
        f.write(f"- **Best Sharpe Ratio:** {max(sharpe_ratios):.2f}\n")
        f.write(f"- **Average Win Rate:** {sum(win_rates) / len(win_rates):.2f}%\n")
        f.write(f"- **Best Win Rate:** {max(win_rates):.2f}%\n")
        f.write(f"- **Profitable Strategies:** {sum(1 for r in returns if r > 0)}\n")
        f.write(f"- **Losing Strategies:** {sum(1 for r in returns if r <= 0)}\n\n")
    
    print(f"\n{'='*80}")
    print(f"📊 Results saved to: {report_path}")
    print(f"{'='*80}")


def generate_configs_with_quantities(base_configs: list, quantities: list = [10, 25, 50, 100]) -> list:
    """Generate configs with varying quantities.
    
    Args:
        base_configs: List of base config dicts with 'name' and 'config' keys
        quantities: List of quantities to test
        
    Returns:
        Expanded list of configs with quantity variations
    """
    expanded = []
    for base in base_configs:
        for qty in quantities:
            config = base["config"].copy()
            config["quantity"] = qty
            name = f"{base['name']} (qty={qty})"
            expanded.append({"name": name, "config": config})
    return expanded


def main():
    """Test many strategy configurations with varying quantities."""
    print("="*80)
    print("COMPREHENSIVE STRATEGY OPTIMIZATION (with quantity variations)")
    print("="*80)
    
    # Base configurations (without quantity - will be varied)
    base_configs = [
        # RSI variations
        {"name": "RSI Default", "config": {"type": "rsi", "period": 14, "oversold": 30, "overbought": 70}},
        {"name": "RSI Long Period", "config": {"type": "rsi", "period": 21, "oversold": 30, "overbought": 70}},
        {"name": "RSI Short Period", "config": {"type": "rsi", "period": 7, "oversold": 30, "overbought": 70}},
        {"name": "RSI Wide Bands", "config": {"type": "rsi", "period": 14, "oversold": 25, "overbought": 75}},
        {"name": "RSI Tight Bands", "config": {"type": "rsi", "period": 14, "oversold": 35, "overbought": 65}},
        
        # Improved RSI
        {"name": "Improved RSI Default", "config": {"type": "rsi_improved", "period": 14, "oversold": 30, "overbought": 70, "exit_rsi": 50}},
        {"name": "Improved RSI Long", "config": {"type": "rsi_improved", "period": 21, "oversold": 30, "overbought": 70, "exit_rsi": 50}},
        
        # RSI with MA Filter
        {"name": "RSI+MA Filter 50", "config": {"type": "rsi_ma_filter", "rsi_period": 14, "ma_period": 50, "oversold": 30, "overbought": 70}},
        
        # MACD variations
        {"name": "MACD Default", "config": {"type": "macd", "fast_period": 12, "slow_period": 26, "signal_period": 9}},
        {"name": "MACD Fast", "config": {"type": "macd", "fast_period": 8, "slow_period": 21, "signal_period": 5}},
        
        # Momentum strategies
        {"name": "Momentum Default", "config": {"type": "momentum", "period": 10, "buy_threshold": 0.5, "sell_threshold": -0.3}},
        {"name": "Momentum Aggressive", "config": {"type": "momentum", "period": 5, "buy_threshold": 0.3, "sell_threshold": -0.2}},
        
        # Bollinger Bands
        {"name": "Bollinger Default", "config": {"type": "bollinger_bands", "period": 20, "std_dev": 2.0}},
        {"name": "Bollinger Wide", "config": {"type": "bollinger_bands", "period": 20, "std_dev": 2.5}},
        
        # RSI + MACD Combo
        {"name": "RSI+MACD Combo", "config": {"type": "rsi_macd_combo", "rsi_period": 14, "oversold": 30, "overbought": 70, "macd_fast": 12, "macd_slow": 26, "macd_signal": 9}},
        
        # Trend Following
        {"name": "Trend Following 10/30/60", "config": {"type": "trend_following", "short_period": 10, "medium_period": 30, "long_period": 60}},
    ]
    
    # Generate configs with varying quantities
    quantities = [10, 25, 50, 100]
    configs = generate_configs_with_quantities(base_configs, quantities)
    
    print(f"Testing {len(configs)} strategy configurations with quantities: {quantities}")
    print("="*80)
    
    results = []
    for i, item in enumerate(configs, 1):
        print(f"\n[{i}/{len(configs)}] Testing: {item['name']}...")
        try:
            metrics = test_strategy_config(item['config'])
            results.append((item['name'], metrics, item['config']))
            print(f"  ✓ Return: ${metrics.total_return:,.2f} ({metrics.total_return_pct:.2f}%) | "
                  f"Trades: {metrics.total_trades} | Win: {metrics.win_rate:.1f}% | "
                  f"Sharpe: {metrics.sharpe_ratio:.2f} | DD: {metrics.max_drawdown_pct:.2f}%")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue
    
    # Sort by total return
    results.sort(key=lambda x: x[1].total_return, reverse=True)
    
    print(f"\n{'='*80}")
    print("TOP 10 STRATEGIES (sorted by return)")
    print(f"{'='*80}")
    print(f"{'Rank':<6} {'Strategy':<30} {'Return %':<12} {'Trades':<8} {'Win %':<8} {'Sharpe':<8} {'Max DD %':<10}")
    print("-" * 90)
    
    for rank, (name, m, config) in enumerate(results[:10], 1):
        print(f"{rank:<6} {name:<30} {m.total_return_pct:>10.2f}%  {m.total_trades:>6}  "
              f"{m.win_rate:>6.1f}%  {m.sharpe_ratio:>6.2f}  {m.max_drawdown_pct:>8.2f}%")
    
    if results:
        best = results[0]
        print(f"\n{'='*80}")
        print("🏆 BEST STRATEGY")
        print(f"{'='*80}")
        print(f"Name: {best[0]}")
        print(f"Config: {best[2]}")
        print(f"Return: ${best[1].total_return:,.2f} ({best[1].total_return_pct:.2f}%)")
        print(f"Trades: {best[1].total_trades}")
        print(f"Win Rate: {best[1].win_rate:.2f}%")
        print(f"Sharpe Ratio: {best[1].sharpe_ratio:.2f}")
        print(f"Max Drawdown: {best[1].max_drawdown_pct:.2f}%")
        print(f"\nTo use this strategy, update config_simulation.json:")
        print(f"  \"strategy\": {best[2]}")
        
        # Save results to markdown file
        save_results_to_markdown(results, best)


if __name__ == "__main__":
    main()

