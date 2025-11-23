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
from trading_lib.strategies import MovingAverageStrategy
from trading_lib.portfolio import SimplePortfolio
from trading_lib.order_manager import OrderManager
from trading_lib.logging_config import setup_logging, get_logger


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
    
    # Create strategy
    strategy = MovingAverageStrategy(short_window=20, long_window=50)
    
    # Create portfolio
    portfolio = SimplePortfolio(cash=100000.0)
    
    # Create order manager
    order_manager = OrderManager(
        portfolio=portfolio,
        max_orders_per_minute=10,
        max_position_size=30000.0,  
        max_order_value=10000.0  
    )
    
    # Create and run trading engine
    engine = TradingEngine(
        gateway=gateway,
        strategy=strategy,
        portfolio=portfolio,
        order_manager=order_manager
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
        logger.info("-" * 50)
        logger.info("Trading session complete.")


if __name__ == "__main__":
    main()

