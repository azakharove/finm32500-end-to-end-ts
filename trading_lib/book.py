"""Order Book implementation with price-time priority matching."""

import heapq
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime

from trading_lib.models import Order, OrderStatus


@dataclass(order=True)
class BookOrder:
    """Order wrapper for heap operations with price-time priority.
    
    For buy orders: Higher price = higher priority (max heap via negation)
    For sell orders: Lower price = higher priority (min heap)
    Time is secondary: Earlier timestamp = higher priority
    """
    
    # Fields for comparison (used by heap)
    priority_price: float = field(compare=True)
    timestamp: datetime = field(compare=True)
    
    # Data fields (not used for comparison)
    order: Order = field(compare=False)
    order_id: str = field(compare=False)


class OrderBook:
    """Order book with price-time priority matching using heaps.
    
    Architecture:
    - Buy orders (bids): Max heap (via negative prices)
    - Sell orders (asks): Min heap
    - Price-time priority: Price first, then timestamp
    - O(log n) insertion, O(log n) matching
    """
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        
        # Heaps for efficient matching
        self._bids: List[BookOrder] = []  # Max heap (negative prices)
        self._asks: List[BookOrder] = []  # Min heap
        
        # Order tracking for modify/cancel
        self._orders: Dict[str, BookOrder] = {}
        self._cancelled_ids: set = set()  # Lazy deletion
        
        # Stats
        self.total_orders = 0
    
    def add_order(self, order: Order) -> str:
        """Add order to book.
        
        Args:
            order: Order to add (quantity > 0 = buy, quantity < 0 = sell)
        
        Returns:
            order_id for tracking
        """
        # Generate order ID
        order_id = f"{self.symbol}_{self.total_orders}"
        self.total_orders += 1
        
        # Create book order with priority
        timestamp = datetime.now()
        
        if order.quantity > 0:  # Buy order
            # Use negative price for max heap behavior
            book_order = BookOrder(
                priority_price=-order.price,  # Negate for max heap
                timestamp=timestamp,
                order=order,
                order_id=order_id
            )
            heapq.heappush(self._bids, book_order)
        else:  # Sell order
            book_order = BookOrder(
                priority_price=order.price,  # Positive for min heap
                timestamp=timestamp,
                order=order,
                order_id=order_id
            )
            heapq.heappush(self._asks, book_order)
        
        # Track for modify/cancel
        self._orders[order_id] = book_order
        
        return order_id
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order (lazy deletion).
        
        Args:
            order_id: ID of order to cancel
        
        Returns:
            True if cancelled, False if not found
        """
        if order_id not in self._orders:
            return False
        
        # Mark as cancelled (lazy deletion - removed during matching)
        self._cancelled_ids.add(order_id)
        del self._orders[order_id]
        
        return True
    
    def modify_order(self, order_id: str, new_price: float = None, new_quantity: int = None) -> bool:
        """Modify an existing order.
        
        Implementation: Cancel old, add new (maintains price-time priority)
        
        Args:
            order_id: ID of order to modify
            new_price: New price (optional)
            new_quantity: New quantity (optional)
        
        Returns:
            True if modified, False if not found
        """
        if order_id not in self._orders:
            return False
        
        # Get old order
        old_book_order = self._orders[order_id]
        old_order = old_book_order.order
        
        # Cancel old order
        self.cancel_order(order_id)
        
        # Create new order with modifications
        new_order = Order(
            symbol=old_order.symbol,
            quantity=new_quantity if new_quantity is not None else old_order.quantity,
            price=new_price if new_price is not None else old_order.price,
            status=OrderStatus.PENDING
        )
        
        # Add new order (gets new timestamp - loses time priority)
        self.add_order(new_order)
        
        return True
    
    def get_matchable_orders(self) -> Optional[tuple]:
        """Get the best bid and ask if they can match.
        
        Returns:
            (best_bid_book_order, best_ask_book_order) if matchable, else None
        """
        # Clean tops
        self._clean_top(self._bids)
        self._clean_top(self._asks)
        
        if not self._bids or not self._asks:
            return None
        
        best_bid = self._bids[0]
        best_ask = self._asks[0]
        
        # Check if they can match
        bid_price = -best_bid.priority_price
        ask_price = best_ask.priority_price
        
        if bid_price >= ask_price:
            return (best_bid, best_ask)
        
        return None
    
    def remove_top_bid(self) -> Optional[BookOrder]:
        """Remove and return the best bid."""
        self._clean_top(self._bids)
        if self._bids:
            book_order = heapq.heappop(self._bids)
            self._orders.pop(book_order.order_id, None)
            return book_order
        return None
    
    def remove_top_ask(self) -> Optional[BookOrder]:
        """Remove and return the best ask."""
        self._clean_top(self._asks)
        if self._asks:
            book_order = heapq.heappop(self._asks)
            self._orders.pop(book_order.order_id, None)
            return book_order
        return None
    
    def get_best_bid(self) -> Optional[float]:
        """Get best bid price (highest buy price)."""
        self._clean_top(self._bids)
        if self._bids:
            return -self._bids[0].priority_price  # Convert from negative
        return None
    
    def get_best_ask(self) -> Optional[float]:
        """Get best ask price (lowest sell price)."""
        self._clean_top(self._asks)
        if self._asks:
            return self._asks[0].priority_price
        return None
    
    def get_spread(self) -> Optional[float]:
        """Get bid-ask spread."""
        bid = self.get_best_bid()
        ask = self.get_best_ask()
        if bid is not None and ask is not None:
            return ask - bid
        return None
    
    def _clean_top(self, heap: List[BookOrder]):
        """Remove cancelled orders from top of heap (lazy deletion cleanup)."""
        while heap and heap[0].order_id in self._cancelled_ids:
            heapq.heappop(heap)
    
    def get_depth(self, levels: int = 5) -> dict:
        """Get order book depth.
        
        Args:
            levels: Number of price levels to return
        
        Returns:
            Dict with bids and asks at each price level
        """
        # Aggregate orders by price level
        bid_levels = {}
        ask_levels = {}
        
        for book_order in self._bids:
            if book_order.order_id not in self._cancelled_ids:
                price = -book_order.priority_price
                bid_levels[price] = bid_levels.get(price, 0) + book_order.order.quantity
        
        for book_order in self._asks:
            if book_order.order_id not in self._cancelled_ids:
                price = book_order.priority_price
                ask_levels[price] = ask_levels.get(price, 0) + abs(book_order.order.quantity)
        
        # Get top N levels
        top_bids = sorted(bid_levels.items(), reverse=True)[:levels]
        top_asks = sorted(ask_levels.items())[:levels]
        
        return {
            'bids': top_bids,
            'asks': top_asks
        }
    
    def __repr__(self):
        """String representation showing best bid/ask."""
        bid = self.get_best_bid()
        ask = self.get_best_ask()
        spread = self.get_spread()
        
        bid_str = f"{bid:.2f}" if bid is not None else "N/A"
        ask_str = f"{ask:.2f}" if ask is not None else "N/A"
        spread_str = f"{spread:.2f}" if spread is not None else "N/A"
        
        return (f"OrderBook({self.symbol}): "
                f"Bid={bid_str}, Ask={ask_str}, Spread={spread_str}")


if __name__ == "__main__":
    from trading_lib.models import Order, OrderStatus
    
    print("="*60)
    print("Non-Matchable Orders")
    print("="*60)
    
    book1 = OrderBook("AAPL")
    book1.add_order(Order("AAPL", 10, 100.0, OrderStatus.PENDING))
    book1.add_order(Order("AAPL", -5, 101.0, OrderStatus.PENDING))
    book1.add_order(Order("AAPL", 20, 99.5, OrderStatus.PENDING))
    
    print(f"\n{book1}")
    print(f"Depth: {book1.get_depth()}")
    
    matchable = book1.get_matchable_orders()
    if matchable:
        bid, ask = matchable
        print(f"\nMatchable: Bid ${-bid.priority_price:.2f} >= Ask ${ask.priority_price:.2f}")
    else:
        print(f"\nNot matchable: Bid ${book1.get_best_bid():.2f} < Ask ${book1.get_best_ask():.2f}")
    
    print("\n" + "="*60)
    print("Matchable Orders")
    print("="*60)
    
    book2 = OrderBook("AAPL")
    book2.add_order(Order("AAPL", 10, 102.0, OrderStatus.PENDING))
    book2.add_order(Order("AAPL", -5, 101.0, OrderStatus.PENDING))
    book2.add_order(Order("AAPL", 15, 101.5, OrderStatus.PENDING))
    book2.add_order(Order("AAPL", -8, 100.5, OrderStatus.PENDING))
    
    print(f"\n{book2}")
    print(f"Depth: {book2.get_depth()}")
    
    matchable = book2.get_matchable_orders()
    if matchable:
        bid, ask = matchable
        bid_price = -bid.priority_price
        ask_price = ask.priority_price
        print(f"\nMatchable: Bid ${bid_price:.2f} >= Ask ${ask_price:.2f}")
        print(f"Best bid: {bid.order.quantity} @ ${bid.order.price:.2f}")
        print(f"Best ask: {abs(ask.order.quantity)} @ ${ask.order.price:.2f}")
    else:
        print(f"\nNot matchable")
    
    print("\n" + "="*60)
