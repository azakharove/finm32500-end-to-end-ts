"""Demo: OrderManager validation and Gateway audit logging."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_lib.gateway import SimulationGateway
from trading_lib.order_manager import OrderManager
from trading_lib.portfolio import SimplePortfolio
from trading_lib.models import Order, OrderStatus

def main():
    # Setup
    portfolio = SimplePortfolio(cash=10000, holdings={})
    
    order_manager = OrderManager(
        portfolio=portfolio,
        max_orders_per_minute=10,
        max_order_value=5000
    )
    
    gateway = SimulationGateway(
        csv_path='AAPL_5d_1m.csv',
        data_dir='data',
        audit_log_path='logs/order_audit.csv'
    )
    
    gateway.connect()
    
    print("="*60)
    print("Order Manager + Gateway Audit Logging Demo")
    print("="*60)
    
    # Test orders
    orders = [
        Order("AAPL", 10, 100.0, OrderStatus.PENDING),   # Valid
        Order("AAPL", 100, 100.0, OrderStatus.PENDING),  # Exceeds value limit
        Order("AAPL", 50, 200.0, OrderStatus.PENDING),   # Exceeds capital
    ]
    
    for i, order in enumerate(orders, 1):
        print(f"\nOrder {i}: {order.symbol} {order.quantity}@${order.price:.2f}")
        
        # Validate through OrderManager
        valid, reason = order_manager.validate_order(order)
        print(f"  Validation: {valid} - {reason}")
        
        if valid:
            # Submit through Gateway (logs to audit file)
            gateway.submit_order(order)
            order_manager.record_order(order)
            print(f"Submitted and logged")
        else:
            print(f"Rejected")
    
    gateway.disconnect()
    
    print("\n" + "="*60)
    print("Check logs/order_audit.csv for audit trail")
    print("="*60)

if __name__ == "__main__":
    main()

