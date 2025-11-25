"""Strategy factory for creating strategies from configuration."""

from typing import Dict, Any

from trading_lib.strategies.base import Strategy
from trading_lib.strategies.moving_average import MovingAverageStrategy
from trading_lib.strategies.rsi import RSIStrategy
from trading_lib.strategies.macd import MACDStrategy
from trading_lib.strategies.rsi_ma_filter import RSIMAFilterStrategy
from trading_lib.strategies.rsi_improved import ImprovedRSIStrategy
from trading_lib.strategies.momentum import MomentumStrategy
from trading_lib.strategies.bollinger_bands import BollingerBandsStrategy
from trading_lib.strategies.rsi_macd_combo import RSIMACDComboStrategy
from trading_lib.strategies.trend_following import TrendFollowingStrategy


def create_strategy(config: Dict[str, Any]) -> Strategy:
    """Create a strategy from configuration.
    
    Args:
        config: Strategy configuration dict with 'type' and parameters
        
    Returns:
        Strategy instance
        
    Example:
        config = {
            "type": "rsi",
            "period": 14,
            "oversold": 30,
            "overbought": 70,
            "quantity": 10
        }
        strategy = create_strategy(config)
    """
    strategy_type = config.get("type", "").lower()
    params = {k: v for k, v in config.items() if k != "type"}
    
    match strategy_type:
        case "moving_average" | "ma":
            return MovingAverageStrategy(**params)
        case "rsi":
            return RSIStrategy(**params)
        case "macd":
            return MACDStrategy(**params)
        case "rsi_ma_filter" | "rsi_ma":
            return RSIMAFilterStrategy(**params)
        case "rsi_improved" | "improved_rsi":
            return ImprovedRSIStrategy(**params)
        case "momentum":
            return MomentumStrategy(**params)
        case "bollinger_bands" | "bb":
            return BollingerBandsStrategy(**params)
        case "rsi_macd_combo" | "rsi_macd":
            return RSIMACDComboStrategy(**params)
        case "trend_following" | "trend":
            return TrendFollowingStrategy(**params)
        case _:
            available = "'moving_average', 'rsi', 'macd', 'rsi_ma_filter', 'rsi_improved', 'momentum', 'bollinger_bands', 'rsi_macd_combo', 'trend_following'"
            raise ValueError(f"Unknown strategy type: {strategy_type}. Available: {available}")

