import random
from typing import Callable
import copy

from trading_lib.models import Order, OrderStatus

# TODO: Matching engine class
    # TODO: process_order and check status of the order (takes order elements)
    # Check how alpaca accepts orders 

# Alpaca: Each order has a unique identifier provided by the client.
    # If the client does not provide one, the system will automatically generate a client-side unique order ID.
    # This ID is returned as part of the order object, along with the other fields.
    # Once an order is placed, it can be queried using either the client-provided order ID or the system-assigned unique ID to check its status.

class MatchingEngine:
    """ Simulates order matching and execution outcomes """
    
    def __init__(self, cancel_rate: float = 0.05, partial_fill_rate: float = 0.1):
        self._orders = {}
        self._cancel_rate = cancel_rate
        self._partial_fill_rate = partial_fill_rate
        self._preset_random_value = None
        self._order_update_callbacks = []

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
    
    def _get_random_value(self) -> float:
        """ Generate a random float between 0 and 1 or return a preset value if specified"""    
        if self._preset_random_value is not None:
            return self._preset_random_value
        return random.random()

    def set_random_value(self, value: float):
        """ Set a preset random value for testing purposes """
        self._preset_random_value = value

    def create_unique_id(self) -> str:
        """ Generate a unique order ID """
        return f"order_{len(self._orders) + 1}_X"
    
    def ensure_order_id(self, order: Order) -> Order:
        """ Ensure the order has a unique ID """
        if not hasattr(order, 'id') or order.id is None:
            order.id = self.create_unique_id()
        return order

    def attempt_to_fill_order(self, order: Order) -> Order:
        """ Simulate order fill attempt based on cancel and partial fill rates """
        random_value = self._get_random_value()
        
        if self._cancel_rate > 0 and random_value < self._cancel_rate:
            order.status = OrderStatus.CANCELED
            order.filled_quantity = 0
        elif self._partial_fill_rate > 0 and random_value < self._partial_fill_rate + self._cancel_rate:
            order.status = OrderStatus.PARTIALLY_FILLED
            order.filled_quantity = order.quantity  // 3 
        else:
            order.status = OrderStatus.FILLED
            order.filled_quantity = order.quantity

        self._orders[order.id] = order

    def process_order(self, order: Order) -> Order:
        " simulate order processing and return status "
        internal_order = copy.copy(order)

        internal_order = self.ensure_order_id(internal_order)
        
        self.attempt_to_fill_order(internal_order)

        self._publish_order_update(internal_order)
        
        return internal_order