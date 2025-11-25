from typing import Dict, List

from trading_lib.strategies.base import Strategy
from trading_lib.models import MarketDataPoint, Action


class TrendFollowingStrategy(Strategy):
    """
    Trend following strategy using multiple moving averages.
    
    - Buys when short MA > medium MA > long MA (strong uptrend)
    - Sells when trend breaks (short MA crosses below medium MA)
    """
    
    def __init__(self, short_period: int = 10, medium_period: int = 30, long_period: int = 60, quantity: int = 10):
        super().__init__(quantity)
        self.short_period = short_period
        self.medium_period = medium_period
        self.long_period = long_period
        self._prices: Dict[str, List[float]] = {}
        self._positions: Dict[str, int] = {}
        self._prev_short_gt_medium: Dict[str, bool] = {}
    
    def _calculate_ma(self, prices: List[float], period: int) -> float:
        """Calculate Simple Moving Average."""
        if len(prices) < period:
            return 0.0
        return sum(prices[-period:]) / period
    
    def generate_signals(self, tick: MarketDataPoint) -> list[tuple]:
        """Generate trading signals based on trend."""
        symbol = tick.symbol
        price = tick.price
        
        if symbol not in self._prices:
            self._prices[symbol] = [price]
            self._positions[symbol] = 0
            self._prev_short_gt_medium[symbol] = False
            return []
        
        self._prices[symbol].append(price)
        prices = self._prices[symbol]
        
        if len(prices) < self.long_period:
            return []
        
        if len(prices) > self.long_period + 10:
            self._prices[symbol] = prices[-(self.long_period + 10):]
            prices = self._prices[symbol]
        
        # Calculate moving averages
        short_ma = self._calculate_ma(prices, self.short_period)
        medium_ma = self._calculate_ma(prices, self.medium_period)
        long_ma = self._calculate_ma(prices, self.long_period)
        
        if short_ma == 0.0 or medium_ma == 0.0 or long_ma == 0.0:
            return []
        
        signals = []
        current_position = self._positions.get(symbol, 0)
        prev_short_gt_medium = self._prev_short_gt_medium.get(symbol, False)
        curr_short_gt_medium = short_ma > medium_ma
        
        # Buy: Strong uptrend (short > medium > long) and no position
        if short_ma > medium_ma > long_ma and current_position == 0:
            signals.append((symbol, self.quantity, price, Action.BUY))
            self._positions[symbol] = self.quantity
        
        # Sell: Trend breaks (short crosses below medium)
        elif prev_short_gt_medium and not curr_short_gt_medium and current_position > 0:
            signals.append((symbol, -self.quantity, price, Action.SELL))
            self._positions[symbol] = 0
        
        self._prev_short_gt_medium[symbol] = curr_short_gt_medium
        
        return signals

