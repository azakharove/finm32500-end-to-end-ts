"""Base Gateway interface for market data and order routing."""

import csv
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Generator, Callable, Optional

from trading_lib.models import MarketDataPoint, Order


class Gateway(ABC):
    """Base class for gateways - handles market data and order routing.
    
    Gateway is the central hub for:
    1. Publishing market data to subscribers
    2. Routing orders to execution venue
    3. Publishing order status updates back to strategy
    4. Audit logging all order events
    """
    
    def __init__(self, audit_log_path: Optional[str] = None):
        self._market_data_callbacks = []
        self._order_update_callbacks = []
        
        # Setup audit logging
        self.audit_log_path = audit_log_path
        self._audit_file = None
        self._audit_writer = None
        
        if audit_log_path:
            self._setup_audit_log(audit_log_path)
    
    # Market Data Subscription
    def subscribe_market_data(self, callback: Callable[[MarketDataPoint], None]):
        """Subscribe to market data updates.
        
        Args:
            callback: Function to call when new market data arrives
        """
        self._market_data_callbacks.append(callback)
    
    def _publish_market_data(self, data_point: MarketDataPoint):
        """Publish market data to all subscribers."""
        for callback in self._market_data_callbacks:
            callback(data_point)
    
    # Order Routing
    @abstractmethod
    def submit_order(self, order: Order) -> None:
        """Submit an order to the execution venue.
        
        Args:
            order: Order to submit
        """
        raise NotImplementedError
    
    # Order Status Updates
    def subscribe_order_updates(self, callback: Callable[[Order], None]):
        """Subscribe to order status updates.
        
        Args:
            callback: Function to call when order status changes
        """
        self._order_update_callbacks.append(callback)
    
    def _publish_order_update(self, order: Order):
        """Publish order update to all subscribers."""
        for callback in self._order_update_callbacks:
            callback(order)
    
    # Gateway Lifecycle
    @abstractmethod
    def connect(self) -> None:
        """Connect to data source and execution venue."""
        raise NotImplementedError
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect and cleanup resources."""
        raise NotImplementedError
    
    @abstractmethod
    def run(self) -> None:
        """Start the gateway (blocking call that processes data)."""
        raise NotImplementedError
    
    # Order Audit Logging
    def _setup_audit_log(self, log_path: str):
        """Setup audit log file."""
        log_file = Path(log_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        self._audit_file = open(log_file, 'a', newline='')
        self._audit_writer = csv.writer(self._audit_file)
        
        # Write header if file is empty
        if log_file.stat().st_size == 0:
            self._audit_writer.writerow([
                'timestamp', 'event', 'symbol', 'quantity', 
                'price', 'order_id', 'status', 'notes'
            ])
            self._audit_file.flush()
    
    def _log_order_event(self, event: str, order: Order, order_id: str = "", notes: str = ""):
        """Log an order event to audit file."""
        if not self._audit_writer:
            return
        
        self._audit_writer.writerow([
            datetime.now().isoformat(),
            event,
            order.symbol,
            order.quantity,
            order.price,
            order_id,
            order.status.value if hasattr(order.status, 'value') else str(order.status),
            notes
        ])
        self._audit_file.flush()
    
    def log_order_sent(self, order: Order, order_id: str = ""):
        """Log when order is sent."""
        self._log_order_event("SENT", order, order_id)
    
    def log_order_modified(self, order: Order, order_id: str = "", notes: str = ""):
        """Log when order is modified."""
        self._log_order_event("MODIFIED", order, order_id, notes)
    
    def log_order_cancelled(self, order: Order, order_id: str = "", notes: str = ""):
        """Log when order is cancelled."""
        self._log_order_event("CANCELLED", order, order_id, notes)
    
    def log_order_filled(self, order: Order, order_id: str = "", fill_price: float = None):
        """Log when order is filled."""
        notes = f"fill_price={fill_price}" if fill_price else ""
        self._log_order_event("FILLED", order, order_id, notes)
    
    def _close_audit_log(self):
        """Close audit log file."""
        if self._audit_file:
            self._audit_file.close()
            self._audit_file = None
            self._audit_writer = None
