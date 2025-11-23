"""Simulation Gateway for backtesting."""

import csv
from pathlib import Path

import pandas as pd

from trading_lib.gateway.base import Gateway
from trading_lib.models import MarketDataPoint, Order


class SimulationGateway(Gateway):
    """Gateway for backtesting with historical CSV data and simulated execution."""
    
    def __init__(self, csv_path: str, data_dir: str = "data", matching_engine=None):
        """Initialize simulation gateway.
        
        Args:
            csv_path: Path to CSV file with historical market data
            data_dir: Directory containing data files
            matching_engine: Optional MatchingEngine for order simulation
        """
        super().__init__()
        self.data_dir = Path(data_dir)
        self.csv_path = self.data_dir / csv_path if not Path(csv_path).is_absolute() else Path(csv_path)
        self.matching_engine = matching_engine
        self._connected = False
        
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")
    
    def connect(self):
        """Connect to simulation data source."""
        print(f"Connected to simulation data: {self.csv_path}")
        self._connected = True
    
    def disconnect(self):
        """Disconnect from simulation."""
        print("Disconnected from simulation")
        self._connected = False
    
    def submit_order(self, order: Order):
        """Submit order to matching engine simulator.
        
        Args:
            order: Order to submit
        """
        if not self._connected:
            raise RuntimeError("Gateway not connected")
        
        # If we have a matching engine, use it to simulate execution
        if self.matching_engine:
            self.matching_engine.process_order(order)
            # Matching engine will call _publish_order_update when order is filled
        else:
            # Simple simulation: immediate fill at order price
            print(f"Simulated order execution: {order.symbol} {order.quantity}@{order.price}")
            self._publish_order_update(order)
    
    def run(self):
        """Stream market data from CSV and publish to subscribers."""
        if not self._connected:
            self.connect()
        
        # Stream data line-by-line
        with open(self.csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data_point = MarketDataPoint(
                    timestamp=pd.to_datetime(row['Datetime']),
                    symbol=row['Symbol'],
                    price=float(row['Close'])
                )
                # Publish to all subscribers
                self._publish_market_data(data_point)

