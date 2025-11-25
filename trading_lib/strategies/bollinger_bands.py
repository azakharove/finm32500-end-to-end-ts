from typing import Dict, List
import math

from trading_lib.strategies.base import Strategy
from trading_lib.models import MarketDataPoint, Action


class BollingerBandsStrategy(Strategy):
    """
    Bollinger Bands mean reversion strategy.
    
    - Buys when price touches lower band (oversold)
    - Sells when price touches upper band (overbought)
    """
    
    def __init__(self, period: int = 20, std_dev: float = 2.0, quantity: int = 10):
        super().__init__(quantity)
        self.period = period
        self.std_dev = std_dev
        self._prices: Dict[str, List[float]] = {}
        self._positions: Dict[str, int] = {}
    
    def _calculate_bollinger_bands(self, prices: List[float]) -> tuple[float, float, float]:
        """Calculate Bollinger Bands.
        
        Returns:
            (upper_band, middle_band, lower_band)
        """
        if len(prices) < self.period:
            return (0.0, 0.0, 0.0)
        
        recent_prices = prices[-self.period:]
        middle_band = sum(recent_prices) / len(recent_prices)
        
        # Calculate standard deviation
        variance = sum((p - middle_band) ** 2 for p in recent_prices) / len(recent_prices)
        std = math.sqrt(variance)
        
        upper_band = middle_band + (self.std_dev * std)
        lower_band = middle_band - (self.std_dev * std)
        
        return (upper_band, middle_band, lower_band)
    
    def generate_signals(self, tick: MarketDataPoint) -> list[tuple]:
        """Generate trading signals based on Bollinger Bands."""
        symbol = tick.symbol
        price = tick.price
        
        if symbol not in self._prices:
            self._prices[symbol] = [price]
            self._positions[symbol] = 0
            return []
        
        self._prices[symbol].append(price)
        prices = self._prices[symbol]
        
        if len(prices) < self.period:
            return []
        
        # Keep only recent prices
        if len(prices) > self.period + 10:
            self._prices[symbol] = prices[-(self.period + 10):]
            prices = self._prices[symbol]
        
        upper_band, middle_band, lower_band = self._calculate_bollinger_bands(prices)
        
        if upper_band == 0.0:
            return []
        
        signals = []
        current_position = self._positions.get(symbol, 0)
        
        # Buy signal: Price touches or goes below lower band (oversold)
        if price <= lower_band and current_position == 0:
            signals.append((symbol, self.quantity, price, Action.BUY))
            self._positions[symbol] = self.quantity
        
        # Sell signal: Price touches or goes above upper band (overbought)
        elif price >= upper_band and current_position > 0:
            signals.append((symbol, -self.quantity, price, Action.SELL))
            self._positions[symbol] = 0
        
        return signals

