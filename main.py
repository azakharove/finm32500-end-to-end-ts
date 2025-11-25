"""
Main entry point for the trading system.

Usage:
    python main.py --config config_simulation.json
    python main.py --config config_live.json
"""
import argparse
import logging
import signal
import sys
import threading
import time
from pathlib import Path

from trading_lib import load_config, create_gateway
from trading_lib.engine import TradingEngine
from trading_lib.strategies.factory import create_strategy
from trading_lib.portfolio import SimplePortfolio
from trading_lib.order_manager import OrderManager
from trading_lib.logging_config import setup_logging, get_logger
from trading_lib.performance import PerformanceTracker


def _generate_equity_curve_graph(timestamps, values, output_path: Path):
    """Generate equity curve graph.
    
    Args:
        timestamps: List of timestamps
        values: List of portfolio values
        output_path: Path to save the graph
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(12, 6))
        plt.plot(timestamps, values, linewidth=2, color='#2E86AB')
        plt.axhline(y=values[0], color='gray', linestyle='--', alpha=0.5, label='Initial Capital')
        plt.fill_between(timestamps, values[0], values, where=[v >= values[0] for v in values], 
                        alpha=0.3, color='green', label='Profit')
        plt.fill_between(timestamps, values[0], values, where=[v < values[0] for v in values], 
                        alpha=0.3, color='red', label='Loss')
        plt.xlabel('Time', fontsize=12)
        plt.ylabel('Portfolio Value ($)', fontsize=12)
        plt.title('Equity Curve', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
    except ImportError:
        pass  # matplotlib not available


def main():
    parser = argparse.ArgumentParser(description="Run the trading system")
    parser.add_argument(
        "--config",
        type=str,
        default="config_simulation.json",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    args = parser.parse_args()
    
    # Initialize logging
    log_level = getattr(logging, args.log_level)
    setup_logging(log_level=log_level)
    logger = get_logger('main')
    
    # Load configuration
    config = load_config(args.config)
    
    # Create gateway
    gateway = create_gateway(config.gateway)
    
    # Create strategy from config
    if config.strategy:
        strategy = create_strategy(config.strategy)
        logger.info(f"Strategy: {type(strategy).__name__} with config: {config.strategy}")
    else:
        # Default strategy if not specified
        from trading_lib.strategies import MovingAverageStrategy
        strategy = MovingAverageStrategy(short_window=20, long_window=50)
        logger.warning("No strategy config found, using default MovingAverageStrategy")
    
    # Create portfolio
    initial_capital = config.initial_capital
    portfolio = SimplePortfolio(cash=initial_capital)
    
    # Create order manager
    order_manager = OrderManager(
        portfolio=portfolio,
        max_orders_per_minute=config.max_orders_per_minute,
        max_position_size=config.max_position_size,
        max_order_value=config.max_order_value
    )
    
    # Create performance tracker for simulation mode
    performance_tracker = None
    if config.gateway.mode == "simulation":
        performance_tracker = PerformanceTracker(initial_capital=initial_capital)
        logger.info("Performance tracking enabled for simulation")
    
    # Create and run trading engine
    engine = TradingEngine(
        gateway=gateway,
        strategy=strategy,
        portfolio=portfolio,
        order_manager=order_manager,
        performance_tracker=performance_tracker
    )
    
    logger.info(f"Starting trading system with config: {args.config}")
    logger.info(f"Mode: {config.gateway.mode}")
    logger.info(f"Gateway: {type(gateway).__name__}")
    logger.info(f"Strategy: {type(strategy).__name__}")
    
    # Sync state for live mode
    if config.gateway.mode == "live":
        from trading_lib.gateway import LiveGateway
        if isinstance(gateway, LiveGateway):
            logger.info("Syncing portfolio state with Alpaca account...")
            try:
                # Connect to gateway first
                gateway.connect()
                
                # Get current state from Alpaca (returns AccountState object)
                account_state = gateway.get_account_state()
                
                # Sync portfolio with actual account state
                # Use buying_power to represent full available capital from Alpaca
                portfolio.sync_state(
                    cash=account_state.buying_power,
                    positions=account_state.positions
                )
                
                # Log current state
                logger.info(f"Account synced:")
                logger.info(f"  Cash: ${account_state.cash:,.2f}")
                logger.info(f"  Buying Power: ${account_state.buying_power:,.2f}")
                logger.info(f"  Portfolio Value: ${account_state.portfolio_value:,.2f}")
                
                if account_state.has_positions:
                    logger.info(f"  Current Positions:")
                    for symbol, pos in account_state.positions.items():
                        pl_pct = (pos.unrealized_plpc * 100) if pos.unrealized_plpc else 0
                        logger.info(f"    {symbol}: {pos.quantity} @ ${pos.avg_price:.2f} "
                                  f"(Current: ${pos.current_price:.2f}, "
                                  f"P/L: ${pos.unrealized_pl:+.2f} ({pl_pct:+.2f}%))")
                    logger.info(f"  Total Unrealized P/L: ${account_state.total_unrealized_pl:+,.2f}")
                
                if account_state.has_open_orders:
                    logger.info(f"  Open Orders ({len(account_state.open_orders)}):")
                    for order in account_state.open_orders:
                        price_str = f"@ ${order.limit_price:.2f}" if order.limit_price else f"(market)"
                        logger.info(f"    [{order.id}] {order.symbol} {order.side} {abs(order.quantity)} {price_str} "
                                  f"(Status: {order.status}, Filled: {order.filled_qty}/{abs(order.quantity)})")
                else:
                    logger.info(f"  No open orders")
                    
            except Exception as e:
                logger.error(f"Failed to sync account state: {e}")
                logger.warning("Continuing with initial portfolio settings...")
    else:
        logger.info(f"Initial capital: ${portfolio.get_cash():,.2f}")
    
    logger.info("-" * 50)
    logger.info("Press Ctrl+C to stop")
    
    # Run the gateway in a background thread
    gateway_thread = threading.Thread(target=engine.run, daemon=True)
    gateway_thread.start()
    
    try:
        # Keep main thread alive and responsive to
        while gateway_thread.is_alive():
            time.sleep(0.1)  # Check every 100ms
    except KeyboardInterrupt:
        logger.info("\n\nShutdown signal received (Ctrl+C)...")
        # Stop the gateway loop
        gateway._connected = False
        # Wait for thread to finish 
        gateway_thread.join(timeout=2.0)
        if gateway_thread.is_alive():
            logger.warning("Gateway thread did not stop cleanly")
    finally:
        # Ensure cleanup happens
        if gateway._connected:
            gateway.disconnect()
        logger.info("-" * 50)
        logger.info("Final portfolio state:")
        logger.info(f"  Cash: ${portfolio.get_cash():,.2f}")
        logger.info(f"  Positions: {portfolio.get_all_holdings()}")
        
        # Write performance metrics to markdown file for simulation mode
        if performance_tracker:
            metrics = performance_tracker.calculate_metrics()
            
            # Generate report filename with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = Path(f"reports/backtest_report_{timestamp}.md")
            report_path.parent.mkdir(exist_ok=True)
            
            # Write markdown report
            with open(report_path, 'w') as f:
                f.write("# Backtest Performance Report\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("---\n\n")
                
                f.write("## Summary\n\n")
                f.write(f"- **Initial Capital:** ${metrics.initial_capital:,.2f}\n")
                f.write(f"- **Final Capital:** ${metrics.final_capital:,.2f}\n")
                f.write(f"- **Total Return:** ${metrics.total_return:,.2f} ({metrics.total_return_pct:.2f}%)\n")
                f.write(f"- **Total P&L:** ${metrics.total_pnl:,.2f}\n\n")
                
                f.write("## Trade Statistics\n\n")
                f.write(f"- **Total Trades:** {metrics.total_trades}\n")
                f.write(f"- **Winning Trades:** {metrics.winning_trades}\n")
                f.write(f"- **Losing Trades:** {metrics.losing_trades}\n")
                if metrics.total_trades > 0:
                    f.write(f"- **Win Rate:** {metrics.win_rate:.2f}%\n")
                    f.write(f"- **Average Win:** ${metrics.avg_win:,.2f}\n")
                    f.write(f"- **Average Loss:** ${metrics.avg_loss:,.2f}\n")
                    f.write(f"- **Profit Factor:** {metrics.profit_factor:.2f}\n")
                f.write("\n")
                
                f.write("## Risk Metrics\n\n")
                f.write(f"- **Max Drawdown:** ${metrics.max_drawdown:,.2f} ({metrics.max_drawdown_pct:.2f}%)\n")
                f.write(f"- **Sharpe Ratio:** {metrics.sharpe_ratio:.2f}\n\n")
                
                # Add equity curve data if available
                timestamps, values = performance_tracker.get_equity_curve_data()
                if timestamps:
                    f.write("## Equity Curve\n\n")
                    f.write(f"Total data points: {len(timestamps)}\n\n")
                    
                    # Generate equity curve graph
                    try:
                        import matplotlib
                        matplotlib.use('Agg')
                        import matplotlib.pyplot as plt
                        
                        graph_path = report_path.parent / f"equity_curve_{timestamp}.png"
                        _generate_equity_curve_graph(timestamps, values, graph_path)
                        f.write(f"![Equity Curve]({graph_path.name})\n\n")
                    except ImportError:
                        pass  # matplotlib not available, skip graph
                    
                    # Also include data table
                    f.write("### Data Points\n\n")
                    f.write("| Timestamp | Portfolio Value |\n")
                    f.write("|-----------|----------------|\n")
                    # Show first 10 and last 10 points
                    for i in range(min(10, len(timestamps))):
                        f.write(f"| {timestamps[i].strftime('%Y-%m-%d %H:%M:%S')} | ${values[i]:,.2f} |\n")
                    if len(timestamps) > 20:
                        f.write("| ... | ... |\n")
                    for i in range(max(10, len(timestamps) - 10), len(timestamps)):
                        f.write(f"| {timestamps[i].strftime('%Y-%m-%d %H:%M:%S')} | ${values[i]:,.2f} |\n")
                    f.write("\n")
                
                # Add trade history if available
                trades = performance_tracker.get_trade_history()
                if trades:
                    f.write("## Trade History\n\n")
                    f.write("| Timestamp | Symbol | Side | Quantity | Price |\n")
                    f.write("|-----------|--------|------|----------|-------|\n")
                    for trade in trades[:50]:  # Limit to first 50 trades
                        f.write(f"| {trade.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {trade.symbol} | {trade.side} | {trade.quantity} | ${trade.price:.2f} |\n")
                    if len(trades) > 50:
                        f.write(f"| ... | ... | ... | ... | ... |\n")
                        f.write(f"*({len(trades) - 50} more trades)*\n")
                    f.write("\n")
            
            logger.info(f"Performance report saved to: {report_path}")
        
        logger.info("-" * 50)
        logger.info("Trading session complete.")


if __name__ == "__main__":
    main()

