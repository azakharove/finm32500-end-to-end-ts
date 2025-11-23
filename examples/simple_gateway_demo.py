"""Simple example showing how to use the Gateway with callbacks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_lib.config import load_config
from trading_lib.factory import create_gateway
from trading_lib.models import MarketDataPoint


def main():
    """Run a simple gateway demo."""
    # Load config
    config = load_config('config_simulation.json')
    gateway = create_gateway(config)
    
    # Counter for stats
    tick_count = 0
    
    # Define callback
    def on_market_data(data_point: MarketDataPoint):
        nonlocal tick_count
        tick_count += 1
        if tick_count % 100 == 0:
            print(f"Tick #{tick_count}: {data_point.symbol} @ ${data_point.price:.2f}")
    
    # Subscribe and run
    gateway.subscribe_market_data(on_market_data)
    gateway.connect()
    
    print("Gateway running... Press Ctrl+C to stop")
    
    try:
        gateway.run()
    except Exception as e:
        print(f"\nStopping... {e}")
    finally:
        gateway.disconnect()
        print(f"\nProcessed {tick_count} ticks total")


if __name__ == "__main__":
    main()

