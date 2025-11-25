from typing import Dict, List

from trading_lib.strategies.base import Strategy
from trading_lib.models import MarketDataPoint, Action


class ImprovedRSIStrategy(Strategy):
    """
    Improved RSI strategy with better exit logic.
    
    - Buys when RSI < oversold
    - Sells when RSI > overbought OR when RSI returns to neutral (50) after being overbought
    - This allows taking profits earlier while still capturing moves
    """
    
    def __init__(self, period: int = 14, oversold: float = 30.0, overbought: float = 70.0, 
                 exit_rsi: float = 50.0, quantity: int = 10):
        super().__init__(quantity)
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.exit_rsi = exit_rsi  # Exit when RSI returns to this level
        self._prices: Dict[str, List[float]] = {}
        self._positions: Dict[str, int] = {}
        self._was_overbought: Dict[str, bool] = {}  # Track if we were overbought
    
    def _calculate_rsi(self, prices: List[float]) -> float:
        """Calculate RSI."""
        if len(prices) < self.period + 1:
            return 50.0
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-self.period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-self.period:]]
        
        avg_gain = sum(gains) / self.period
        avg_loss = sum(losses) / self.period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_signals(self, tick: MarketDataPoint) -> list[tuple]:
        """Generate trading signals with improved exit logic."""
        symbol = tick.symbol
        price = tick.price
        
        if symbol not in self._prices:
            self._prices[symbol] = [price]
            self._positions[symbol] = 0
            self._was_overbought[symbol] = False
            return []
        
        self._prices[symbol].append(price)
        prices = self._prices[symbol]
        
        if len(prices) < self.period + 1:
            return []
        
        if len(prices) > self.period + 1:
            self._prices[symbol] = prices[-(self.period + 1):]
            prices = self._prices[symbol]
        
        rsi = self._calculate_rsi(prices)
        signals = []
        current_position = self._positions.get(symbol, 0)
        was_overbought = self._was_overbought.get(symbol, False)
        
        # Buy signal: RSI oversold and no position
        if rsi < self.oversold and current_position == 0:
            signals.append((symbol, self.quantity, price, Action.BUY))
            self._positions[symbol] = self.quantity
            self._was_overbought[symbol] = False
        
        # Sell signal: RSI overbought (immediate exit) OR RSI returns to neutral after being overbought
        elif current_position > 0:
            if rsi > self.overbought:
                signals.append((symbol, -self.quantity, price, Action.SELL))
                self._positions[symbol] = 0
                self._was_overbought[symbol] = True
            elif was_overbought and rsi <= self.exit_rsi:
                # Exit when RSI returns to neutral after being overbought (take profit)
                signals.append((symbol, -self.quantity, price, Action.SELL))
                self._positions[symbol] = 0
                self._was_overbought[symbol] = False
        
        # Update overbought tracking
        if rsi > self.overbought:
            self._was_overbought[symbol] = True
        elif rsi < self.oversold:
            self._was_overbought[symbol] = False
        
        return signals

