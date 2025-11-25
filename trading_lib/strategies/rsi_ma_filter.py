from typing import Dict, List

from trading_lib.strategies.base import Strategy
from trading_lib.models import MarketDataPoint, Action


class RSIMAFilterStrategy(Strategy):
    """
    RSI strategy with Moving Average filter.
    
    Only trades when:
    - Price is above MA (uptrend) for buy signals
    - Price is below MA (downtrend) for sell signals
    
    This filters out trades against the trend.
    """
    
    def __init__(self, rsi_period: int = 14, ma_period: int = 50, oversold: float = 30.0, 
                 overbought: float = 70.0, quantity: int = 10):
        super().__init__(quantity)
        self.rsi_period = rsi_period
        self.ma_period = ma_period
        self.oversold = oversold
        self.overbought = overbought
        self._prices: Dict[str, List[float]] = {}
        self._positions: Dict[str, int] = {}
    
    def _calculate_rsi(self, prices: List[float]) -> float:
        """Calculate RSI."""
        if len(prices) < self.rsi_period + 1:
            return 50.0
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-self.rsi_period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-self.rsi_period:]]
        
        avg_gain = sum(gains) / self.rsi_period
        avg_loss = sum(losses) / self.rsi_period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_ma(self, prices: List[float]) -> float:
        """Calculate Moving Average."""
        if len(prices) < self.ma_period:
            return 0.0
        return sum(prices[-self.ma_period:]) / self.ma_period
    
    def generate_signals(self, tick: MarketDataPoint) -> list[tuple]:
        """Generate trading signals with MA filter."""
        symbol = tick.symbol
        price = tick.price
        
        if symbol not in self._prices:
            self._prices[symbol] = [price]
            self._positions[symbol] = 0
            return []
        
        self._prices[symbol].append(price)
        prices = self._prices[symbol]
        
        # Need enough prices for both RSI and MA
        min_prices = max(self.rsi_period + 1, self.ma_period)
        if len(prices) < min_prices:
            return []
        
        # Keep only recent prices
        if len(prices) > min_prices + 10:
            self._prices[symbol] = prices[-min_prices - 10:]
            prices = self._prices[symbol]
        
        # Calculate indicators
        rsi = self._calculate_rsi(prices)
        ma = self._calculate_ma(prices)
        
        if ma == 0.0:
            return []
        
        signals = []
        current_position = self._positions.get(symbol, 0)
        
        # Buy: RSI oversold AND price above MA (uptrend)
        if rsi < self.oversold and price > ma and current_position == 0:
            signals.append((symbol, self.quantity, price, Action.BUY))
            self._positions[symbol] = self.quantity
        
        # Sell: RSI overbought OR price below MA (downtrend)
        elif (rsi > self.overbought or price < ma) and current_position > 0:
            signals.append((symbol, -self.quantity, price, Action.SELL))
            self._positions[symbol] = 0
        
        return signals

