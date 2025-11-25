"""Simulation Gateway for backtesting."""

import csv
from pathlib import Path

import pandas as pd

from trading_lib.gateway.base import Gateway
from trading_lib.models import MarketDataPoint, Order
from trading_lib.logging_config import get_logger


class SimulationGateway(Gateway):
    """Gateway for backtesting with historical CSV data and simulated execution."""
    
    def __init__(self, csv_path: str, data_dir: str = "data", matching_engine=None, audit_log_path: str = None):
        """Initialize simulation gateway.
        
        Args:
            csv_path: Path to CSV file with historical market data
            data_dir: Directory containing data files
            matching_engine: Optional MatchingEngine for order simulation
            audit_log_path: Optional path for order audit log
        """
        super().__init__(audit_log_path=audit_log_path)
        self.data_dir = Path(data_dir)
        self.csv_path = self.data_dir / csv_path if not Path(csv_path).is_absolute() else Path(csv_path)
        self._connected = False
        self.logger = get_logger('gateway.simulation')

        self.matching_engine = matching_engine
        if self.matching_engine:
            self.matching_engine.subscribe_order_updates(self._publish_order_update)
        
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")
        
    
    def connect(self):
        """Connect to simulation data source."""
        self.logger.info(f"Connected to simulation data: {self.csv_path}")
        self._connected = True
    
    def disconnect(self):
        """Disconnect from simulation."""
        self._close_audit_log()
        self.logger.info("Disconnected from simulation")
        self._connected = False
    
    def submit_order(self, order: Order):
        """Submit order to matching engine simulator.
        
        Args:
            order: Order to submit
        """
        if not self._connected:
            raise RuntimeError("Gateway not connected")
        
        # Log order submission
        self.log_order_sent(order)
        
        # If we have a matching engine, use it to simulate execution
        if self.matching_engine:
            self.matching_engine.process_order(order)
            # Matching engine will call _publish_order_update when order is filled
        else:
            # Simple simulation: immediate fill at order price
            from trading_lib.models import OrderStatus
            # Set filled_quantity to full quantity and status to FILLED
            order.filled_quantity = abs(order.quantity)
            order.status = OrderStatus.FILLED
            self.logger.debug(f"Simulated order execution: {order.symbol} {order.quantity}@{order.price}")
            self.log_order_filled(order, fill_price=order.price)
            self._publish_order_update(order)
    
    def run(self):
        """Stream market data from CSV and publish to subscribers."""
        if not self._connected:
            self.connect()
        
        try:
            # Stream data line-by-line
            with open(self.csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Check if we should stop
                    if not self._connected:
                        self.logger.info("Simulation stopped by disconnect signal")
                        break
                    
                    data_point = MarketDataPoint(
                        timestamp=pd.to_datetime(row['Datetime']),
                        symbol=row['Symbol'],
                        price=float(row['Close'])
                    )
                    # Publish to all subscribers
                    self._publish_market_data(data_point)
        except KeyboardInterrupt:
            self.logger.info("Simulation interrupted")
            raise

