"""Trading library for backtesting and execution."""

from trading_lib.models import MarketDataPoint, Order, OrderStatus, Action, RecordingInterval
from trading_lib.exceptions import ExecutionError, OrderError
from trading_lib.engine import ExecutionEngine
from trading_lib.data_loader import DataLoader
from trading_lib.config import load_config, TradingConfig, GatewayConfig
from trading_lib.factory import create_gateway

__all__ = [
    "MarketDataPoint",
    "Order",
    "OrderStatus",
    "Action",
    "RecordingInterval",
    "ExecutionError",
    "OrderError",
    "ExecutionEngine",
    "DataLoader",
    "load_config",
    "TradingConfig",
    "GatewayConfig",
    "create_gateway",
]

