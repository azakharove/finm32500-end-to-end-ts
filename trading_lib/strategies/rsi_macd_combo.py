from typing import Dict, List

from trading_lib.strategies.base import Strategy
from trading_lib.models import MarketDataPoint, Action


class RSIMACDComboStrategy(Strategy):
    """
    Combined RSI + MACD strategy.
    
    Requires BOTH indicators to agree:
    - Buy: RSI oversold AND MACD bullish crossover
    - Sell: RSI overbought OR MACD bearish crossover
    """
    
    def __init__(self, rsi_period: int = 14, oversold: float = 30.0, overbought: float = 70.0,
                 macd_fast: int = 12, macd_slow: int = 26, macd_signal: int = 9, quantity: int = 10):
        super().__init__(quantity)
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self._prices: Dict[str, List[float]] = {}
        self._positions: Dict[str, int] = {}
        self._prev_macd_above_signal: Dict[str, bool] = {}
    
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
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return 0.0
        
        sma = sum(prices[:period]) / period
        multiplier = 2.0 / (period + 1)
        
        ema = sma
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def _calculate_macd(self, prices: List[float]) -> tuple[float, float]:
        """Calculate MACD line and signal line.
        
        Returns:
            (macd_line, signal_line)
        """
        min_prices = self.macd_slow + self.macd_signal
        if len(prices) < min_prices:
            return (0.0, 0.0)
        
        fast_ema = self._calculate_ema(prices, self.macd_fast)
        slow_ema = self._calculate_ema(prices, self.macd_slow)
        macd_line = fast_ema - slow_ema
        
        # Simplified signal line calculation
        if len(prices) >= min_prices:
            macd_values = []
            for i in range(self.macd_slow, len(prices)):
                fast = self._calculate_ema(prices[:i+1], self.macd_fast)
                slow = self._calculate_ema(prices[:i+1], self.macd_slow)
                macd_values.append(fast - slow)
            
            if len(macd_values) >= self.macd_signal:
                signal_line = self._calculate_ema(macd_values, self.macd_signal)
            else:
                signal_line = macd_line
        else:
            signal_line = macd_line
        
        return (macd_line, signal_line)
    
    def generate_signals(self, tick: MarketDataPoint) -> list[tuple]:
        """Generate trading signals based on RSI + MACD combination."""
        symbol = tick.symbol
        price = tick.price
        
        if symbol not in self._prices:
            self._prices[symbol] = [price]
            self._positions[symbol] = 0
            self._prev_macd_above_signal[symbol] = False
            return []
        
        self._prices[symbol].append(price)
        prices = self._prices[symbol]
        
        min_prices = max(self.rsi_period + 1, self.macd_slow + self.macd_signal)
        if len(prices) < min_prices:
            return []
        
        if len(prices) > min_prices + 20:
            self._prices[symbol] = prices[-(min_prices + 20):]
            prices = self._prices[symbol]
        
        # Calculate indicators
        rsi = self._calculate_rsi(prices)
        macd_line, signal_line = self._calculate_macd(prices)
        
        if macd_line == 0.0 and signal_line == 0.0:
            return []
        
        signals = []
        current_position = self._positions.get(symbol, 0)
        prev_above = self._prev_macd_above_signal.get(symbol, False)
        curr_above = macd_line > signal_line
        
        # Buy: RSI oversold AND MACD bullish crossover
        if rsi < self.oversold and not prev_above and curr_above and current_position == 0:
            signals.append((symbol, self.quantity, price, Action.BUY))
            self._positions[symbol] = self.quantity
        
        # Sell: RSI overbought OR MACD bearish crossover
        elif current_position > 0:
            if rsi > self.overbought or (prev_above and not curr_above):
                signals.append((symbol, -self.quantity, price, Action.SELL))
                self._positions[symbol] = 0
        
        self._prev_macd_above_signal[symbol] = curr_above
        
        return signals

