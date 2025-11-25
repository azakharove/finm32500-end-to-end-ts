from typing import Dict, List

from trading_lib.strategies.base import Strategy
from trading_lib.models import MarketDataPoint, Action


class MACDStrategy(Strategy):
    """
    MACD (Moving Average Convergence Divergence) strategy.
    
    - Buys when MACD line crosses above signal line (bullish crossover)
    - Sells when MACD line crosses below signal line (bearish crossover)
    """
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9, quantity: int = 10):
        super().__init__(quantity)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self._prices: Dict[str, List[float]] = {}
        self._positions: Dict[str, int] = {}  # Track current position per symbol
        self._prev_macd_above_signal: Dict[str, bool] = {}  # Track previous crossover state
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return 0.0
        
        # Start with SMA
        sma = sum(prices[:period]) / period
        multiplier = 2.0 / (period + 1)
        
        ema = sma
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def _calculate_macd(self, prices: List[float]) -> tuple[float, float, float]:
        """Calculate MACD, Signal, and Histogram.
        
        Returns:
            (macd_line, signal_line, histogram)
        """
        if len(prices) < self.slow_period + self.signal_period:
            return (0.0, 0.0, 0.0)
        
        # Calculate fast and slow EMAs
        fast_ema = self._calculate_ema(prices, self.fast_period)
        slow_ema = self._calculate_ema(prices, self.slow_period)
        
        macd_line = fast_ema - slow_ema
        
        # Calculate signal line (EMA of MACD)
        # We need MACD values over time for signal line
        # For simplicity, use recent prices to approximate
        if len(prices) >= self.slow_period + self.signal_period:
            # Calculate MACD values for signal line
            macd_values = []
            for i in range(self.slow_period, len(prices)):
                fast = self._calculate_ema(prices[:i+1], self.fast_period)
                slow = self._calculate_ema(prices[:i+1], self.slow_period)
                macd_values.append(fast - slow)
            
            if len(macd_values) >= self.signal_period:
                signal_line = self._calculate_ema(macd_values, self.signal_period)
            else:
                signal_line = macd_line
        else:
            signal_line = macd_line
        
        histogram = macd_line - signal_line
        
        return (macd_line, signal_line, histogram)
    
    def generate_signals(self, tick: MarketDataPoint) -> list[tuple]:
        """Generate trading signals based on MACD crossover."""
        symbol = tick.symbol
        price = tick.price
        
        # Initialize for symbol
        if symbol not in self._prices:
            self._prices[symbol] = [price]
            self._positions[symbol] = 0
            self._prev_macd_above_signal[symbol] = False
            return []
        
        # Add current price
        self._prices[symbol].append(price)
        prices = self._prices[symbol]
        
        # Need enough prices for MACD calculation
        min_prices = self.slow_period + self.signal_period
        if len(prices) < min_prices:
            return []
        
        # Keep only recent prices (keep more for EMA calculation)
        if len(prices) > min_prices + 20:
            self._prices[symbol] = prices[-(min_prices + 20):]
            prices = self._prices[symbol]
        
        # Calculate MACD
        macd_line, signal_line, histogram = self._calculate_macd(prices)
        
        # Skip if MACD not ready
        if macd_line == 0.0 and signal_line == 0.0:
            return []
        
        signals = []
        current_position = self._positions.get(symbol, 0)
        prev_above = self._prev_macd_above_signal.get(symbol, False)
        curr_above = macd_line > signal_line
        
        # Buy signal: MACD crosses above signal (bullish crossover) and no position
        if not prev_above and curr_above and current_position == 0:
            signals.append((symbol, self.quantity, price, Action.BUY))
            self._positions[symbol] = self.quantity
        
        # Sell signal: MACD crosses below signal (bearish crossover) and have position
        elif prev_above and not curr_above and current_position > 0:
            signals.append((symbol, -self.quantity, price, Action.SELL))
            self._positions[symbol] = 0
        
        # Update previous state
        self._prev_macd_above_signal[symbol] = curr_above
        
        return signals

