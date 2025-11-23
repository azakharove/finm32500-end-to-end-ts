"""Trading strategies module."""

from trading_lib.strategies.base import Strategy
from trading_lib.strategies.moving_average import MovingAverageStrategy

__all__ = ["Strategy", "MovingAverageStrategy"]

