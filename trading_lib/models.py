from dataclasses import dataclass
from datetime import datetime
from enum import Enum


@dataclass(frozen=True)
class MarketDataPoint:
    """Frozen dataclass representing a market data point."""

    timestamp: datetime
    symbol: str
    price: float

class OrderStatus(str, Enum):
    """Enum representing the status of an order."""

    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELED = "CANCELED"
    FAILED = "FAILED"

class Order:
    """Mutable class representing a trade order."""

    def __init__(self, symbol: str, quantity: int, price: float, status: OrderStatus, id: str | None = None):
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.status = status
        self.id = id
        
class Action(str, Enum):
    """Enum representing the action of an order."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class RecordingInterval(str, Enum):
    """Enum representing the frequency of portfolio value recording."""
    
    TICK = "tick"           # Every tick (very high frequency)
    SECOND = "1s"           # Every 1 second
    MINUTE = "1m"           # Every 1 minute
    HOURLY = "1h"           # Every hour
    DAILY = "1d"            # Once per day
    WEEKLY = "1w"           # Once per week
    MONTHLY = "1mo"         # Once per month


# Alpaca-specific models for external API integration

@dataclass(frozen=True)
class AlpacaPosition:
    """Represents a position from Alpaca API."""
    
    symbol: str
    quantity: int
    avg_price: float
    current_price: float
    market_value: float
    unrealized_pl: float
    unrealized_plpc: float = 0.0  # P/L percentage
    
    @classmethod
    def from_alpaca_position(cls, pos):
        """Create AlpacaPosition from Alpaca API position object."""
        return cls(
            symbol=pos.symbol,
            quantity=int(pos.qty),
            avg_price=float(pos.avg_entry_price),
            current_price=float(pos.current_price),
            market_value=float(pos.market_value),
            unrealized_pl=float(pos.unrealized_pl),
            unrealized_plpc=float(pos.unrealized_plpc) if hasattr(pos, 'unrealized_plpc') else 0.0
        )


@dataclass(frozen=True)
class AlpacaOrder:
    """Represents an order from Alpaca API."""
    
    id: str
    symbol: str
    quantity: int  # Negative for sell orders
    side: str  # 'buy' or 'sell'
    order_type: str  # 'market', 'limit', 'stop', etc.
    limit_price: float | None
    stop_price: float | None
    status: str  # 'new', 'partially_filled', 'filled', 'canceled', etc.
    submitted_at: datetime
    filled_qty: int
    filled_avg_price: float | None
    
    @classmethod
    def from_alpaca_order(cls, order):
        """Create AlpacaOrder from Alpaca API order object."""
        return cls(
            id=order.id,
            symbol=order.symbol,
            quantity=int(order.qty) if order.side == 'buy' else -int(order.qty),
            side=order.side,
            order_type=order.type,
            limit_price=float(order.limit_price) if order.limit_price else None,
            stop_price=float(order.stop_price) if hasattr(order, 'stop_price') and order.stop_price else None,
            status=order.status,
            submitted_at=order.submitted_at,
            filled_qty=int(order.filled_qty) if order.filled_qty else 0,
            filled_avg_price=float(order.filled_avg_price) if hasattr(order, 'filled_avg_price') and order.filled_avg_price else None
        )


@dataclass(frozen=True)
class AccountState:
    """Represents the current state of a trading account."""
    
    cash: float
    buying_power: float
    portfolio_value: float
    positions: dict[str, AlpacaPosition]  # symbol -> position
    open_orders: list[AlpacaOrder]
    
    @property
    def has_positions(self) -> bool:
        """Check if account has any open positions."""
        return len(self.positions) > 0
    
    @property
    def has_open_orders(self) -> bool:
        """Check if account has any open orders."""
        return len(self.open_orders) > 0
    
    @property
    def total_unrealized_pl(self) -> float:
        """Calculate total unrealized P/L across all positions."""
        return sum(pos.unrealized_pl for pos in self.positions.values())
