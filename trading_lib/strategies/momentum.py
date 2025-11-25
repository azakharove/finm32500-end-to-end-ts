from typing import Dict, List

from trading_lib.strategies.base import Strategy
from trading_lib.models import MarketDataPoint, Action


class MomentumStrategy(Strategy):
    """
    Momentum strategy based on price rate of change.
    
    - Buys when price momentum is strong (ROC > threshold)
    - Sells when momentum weakens (ROC < -threshold or crosses below zero)
    """
    
    def __init__(self, period: int = 10, buy_threshold: float = 0.5, sell_threshold: float = -0.3, quantity: int = 10):
        super().__init__(quantity)
        self.period = period
        self.buy_threshold = buy_threshold  # ROC % to trigger buy
        self.sell_threshold = sell_threshold  # ROC % to trigger sell
        self._prices: Dict[str, List[float]] = {}
        self._positions: Dict[str, int] = {}
        self._entry_prices: Dict[str, float] = {}  # Track entry price for stop-loss
    
    def _calculate_roc(self, prices: List[float]) -> float:
        """Calculate Rate of Change (ROC) percentage."""
        if len(prices) < self.period + 1:
            return 0.0
        
        current_price = prices[-1]
        past_price = prices[-self.period - 1]
        
        if past_price == 0:
            return 0.0
        
        roc = ((current_price - past_price) / past_price) * 100
        return roc
    
    def generate_signals(self, tick: MarketDataPoint) -> list[tuple]:
        """Generate trading signals based on momentum."""
        symbol = tick.symbol
        price = tick.price
        
        if symbol not in self._prices:
            self._prices[symbol] = [price]
            self._positions[symbol] = 0
            return []
        
        self._prices[symbol].append(price)
        prices = self._prices[symbol]
        
        if len(prices) < self.period + 1:
            return []
        
        # Keep only recent prices
        if len(prices) > self.period + 20:
            self._prices[symbol] = prices[-(self.period + 20):]
            prices = self._prices[symbol]
        
        roc = self._calculate_roc(prices)
        signals = []
        current_position = self._positions.get(symbol, 0)
        
        # Buy signal: Strong positive momentum and no position
        if roc > self.buy_threshold and current_position == 0:
            signals.append((symbol, self.quantity, price, Action.BUY))
            self._positions[symbol] = self.quantity
            self._entry_prices[symbol] = price
        
        # Sell signal: Momentum weakens or turns negative
        elif current_position > 0:
            if roc < self.sell_threshold or roc < 0:
                signals.append((symbol, -self.quantity, price, Action.SELL))
                self._positions[symbol] = 0
                self._entry_prices.pop(symbol, None)
        
        return signals

