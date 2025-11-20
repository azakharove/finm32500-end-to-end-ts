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
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Order:
    """Mutable class representing a trade order."""

    def __init__(self, symbol: str, quantity: int, price: float, status: OrderStatus):
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.status = status

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
