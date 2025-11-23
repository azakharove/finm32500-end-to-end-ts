"""Base Gateway interface for market data and order routing."""

from abc import ABC, abstractmethod
from typing import Generator, Callable, Optional

from trading_lib.models import MarketDataPoint, Order


class Gateway(ABC):
    """Base class for gateways - handles market data and order routing.
    
    Gateway is the central hub for:
    1. Publishing market data to subscribers
    2. Routing orders to execution venue
    3. Publishing order status updates back to strategy
    """
    
    def __init__(self):
        self._market_data_callbacks = []
        self._order_update_callbacks = []
    
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
