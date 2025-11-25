from typing import Dict, List

from trading_lib.strategies.base import Strategy
from trading_lib.models import MarketDataPoint, Action


class RSIStrategy(Strategy):
    """
    RSI (Relative Strength Index) strategy.
    
    - Buys when RSI < 30 (oversold)
    - Sells when RSI > 70 (overbought)
    - Holds otherwise
    """
    
    def __init__(self, period: int = 14, oversold: float = 30.0, overbought: float = 70.0, quantity: int = 10):
        super().__init__(quantity)
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self._prices: Dict[str, List[float]] = {}
        self._positions: Dict[str, int] = {}  # Track current position per symbol
    
    def _calculate_rsi(self, prices: List[float]) -> float:
        """Calculate RSI for a list of prices.
        
        Args:
            prices: List of prices (must be at least period+1 long)
            
        Returns:
            RSI value (0-100)
        """
        if len(prices) < self.period + 1:
            return 50.0  # Neutral RSI
        
        # Calculate price changes
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        # Separate gains and losses
        gains = [d if d > 0 else 0 for d in deltas[-self.period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-self.period:]]
        
        # Calculate average gain and loss
        avg_gain = sum(gains) / self.period
        avg_loss = sum(losses) / self.period
        
        if avg_loss == 0:
            return 100.0  # All gains, no losses
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def generate_signals(self, tick: MarketDataPoint) -> list[tuple]:
        """Generate trading signals based on RSI.
        
        Returns:
            List of (symbol, quantity, price, action) tuples
        """
        symbol = tick.symbol
        price = tick.price
        
        # Initialize price history for symbol
        if symbol not in self._prices:
            self._prices[symbol] = [price]
            self._positions[symbol] = 0
            return []
        
        # Add current price
        self._prices[symbol].append(price)
        prices = self._prices[symbol]
        
        # Need at least period+1 prices to calculate RSI
        if len(prices) < self.period + 1:
            return []
        
        # Keep only recent prices (period+1 is enough)
        if len(prices) > self.period + 1:
            self._prices[symbol] = prices[-(self.period + 1):]
            prices = self._prices[symbol]
        
        # Calculate RSI
        rsi = self._calculate_rsi(prices)
        
        signals = []
        current_position = self._positions.get(symbol, 0)
        
        # Buy signal: RSI oversold and no position
        if rsi < self.oversold and current_position == 0:
            signals.append((symbol, self.quantity, price, Action.BUY))
            self._positions[symbol] = self.quantity
        
        # Sell signal: RSI overbought and have position
        elif rsi > self.overbought and current_position > 0:
            signals.append((symbol, -self.quantity, price, Action.SELL))
            self._positions[symbol] = 0
        
        return signals

