"""Performance tracking and metrics calculation for trading strategies."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List
import math

from trading_lib.models import Order, MarketDataPoint
from trading_lib.portfolio import Portfolio


@dataclass
class Trade:
    """Represents a single executed trade."""
    timestamp: datetime
    symbol: str
    quantity: int  # Positive for buy, negative for sell
    price: float
    side: str  # 'buy' or 'sell'
    order_id: Optional[str] = None


@dataclass
class Position:
    """Represents an open position."""
    symbol: str
    quantity: int
    avg_entry_price: float
    current_price: float = 0.0
    
    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized P&L."""
        return (self.current_price - self.avg_entry_price) * self.quantity
    
    @property
    def unrealized_pnl_pct(self) -> float:
        """Calculate unrealized P&L percentage."""
        if self.avg_entry_price == 0:
            return 0.0
        return ((self.current_price - self.avg_entry_price) / self.avg_entry_price) * 100


@dataclass
class PerformanceMetrics:
    """Performance metrics for a trading strategy."""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    total_return: float = 0.0
    total_return_pct: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    initial_capital: float = 0.0
    final_capital: float = 0.0


class PerformanceTracker:
    """Tracks trading performance and calculates metrics.
    
    Records:
    - All executed trades
    - Portfolio value over time (equity curve)
    - Open positions
    - Performance metrics
    """
    
    def __init__(self, initial_capital: float):
        """Initialize performance tracker.
        
        Args:
            initial_capital: Starting capital for the strategy
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        # Trade history
        self.trades: List[Trade] = []
        
        # Equity curve: timestamp -> portfolio value
        self.equity_curve: List[tuple[datetime, float]] = []
        
        # Open positions: symbol -> Position
        self.positions: Dict[str, Position] = {}
        
        # Closed position P&L tracking
        self.closed_pnls: List[float] = []  # P&L for each closed position
        
        # Current prices for unrealized P&L
        self.current_prices: Dict[str, float] = {}
    
    def record_trade(self, order: Order, timestamp: Optional[datetime] = None):
        """Record an executed trade.
        
        Args:
            order: The filled order
            timestamp: Trade timestamp (default: now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        trade = Trade(
            timestamp=timestamp,
            symbol=order.symbol,
            quantity=order.quantity,
            price=order.price,
            side='buy' if order.quantity > 0 else 'sell'
        )
        self.trades.append(trade)
        
        # Update position tracking
        self._update_position(trade)
    
    def _update_position(self, trade: Trade):
        """Update position tracking based on trade."""
        symbol = trade.symbol
        
        if symbol not in self.positions:
            # New position
            if trade.quantity != 0:  # Only create if non-zero
                self.positions[symbol] = Position(
                    symbol=symbol,
                    quantity=trade.quantity,
                    avg_entry_price=trade.price,
                    current_price=trade.price
                )
        else:
            # Update existing position
            pos = self.positions[symbol]
            old_quantity = pos.quantity
            new_quantity = old_quantity + trade.quantity
            
            if new_quantity == 0:
                # Position closed - calculate P&L
                if old_quantity > 0:  # Was long
                    pnl = (trade.price - pos.avg_entry_price) * abs(old_quantity)
                else:  # Was short
                    pnl = (pos.avg_entry_price - trade.price) * abs(old_quantity)
                self.closed_pnls.append(pnl)
                del self.positions[symbol]
            else:
                # Update position
                # Recalculate average entry price
                if (old_quantity > 0 and trade.quantity > 0) or (old_quantity < 0 and trade.quantity < 0):
                    # Adding to position - update average
                    total_cost = (pos.avg_entry_price * abs(old_quantity)) + (trade.price * abs(trade.quantity))
                    pos.avg_entry_price = total_cost / abs(new_quantity)
                
                pos.quantity = new_quantity
                pos.current_price = trade.price
    
    def update_market_price(self, symbol: str, price: float):
        """Update current market price for a symbol.
        
        Args:
            symbol: Symbol to update
            price: Current market price
        """
        self.current_prices[symbol] = price
        if symbol in self.positions:
            self.positions[symbol].current_price = price
    
    def record_portfolio_value(self, portfolio: Portfolio, timestamp: Optional[datetime] = None):
        """Record current portfolio value for equity curve.
        
        Args:
            portfolio: Portfolio to get value from
            timestamp: Timestamp for recording (default: now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Update current prices in positions
        for symbol in self.positions:
            if symbol in self.current_prices:
                self.positions[symbol].current_price = self.current_prices[symbol]
        
        # Calculate total portfolio value
        portfolio_value = portfolio.get_portfolio_value(self.current_prices)
        self.equity_curve.append((timestamp, portfolio_value))
        self.current_capital = portfolio_value
    
    def calculate_metrics(self) -> PerformanceMetrics:
        """Calculate performance metrics.
        
        Returns:
            PerformanceMetrics object with all calculated metrics
        """
        if not self.trades:
            return PerformanceMetrics(initial_capital=self.initial_capital, final_capital=self.current_capital)
        
        # Basic trade statistics
        total_trades = len(self.trades)
        
        # Calculate P&L from closed positions
        winning_trades = sum(1 for pnl in self.closed_pnls if pnl > 0)
        losing_trades = sum(1 for pnl in self.closed_pnls if pnl < 0)
        total_pnl = sum(self.closed_pnls)
        
        # Add unrealized P&L from open positions
        unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        total_pnl += unrealized_pnl
        
        # Returns
        total_return = self.current_capital - self.initial_capital
        total_return_pct = (total_return / self.initial_capital * 100) if self.initial_capital > 0 else 0.0
        
        # Win rate
        closed_trades = len(self.closed_pnls)
        win_rate = (winning_trades / closed_trades * 100) if closed_trades > 0 else 0.0
        
        # Average win/loss
        wins = [pnl for pnl in self.closed_pnls if pnl > 0]
        losses = [pnl for pnl in self.closed_pnls if pnl < 0]
        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = abs(sum(losses) / len(losses)) if losses else 0.0
        
        # Profit factor
        gross_profit = sum(wins) if wins else 0.0
        gross_loss = abs(sum(losses)) if losses else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0.0)
        
        # Sharpe ratio (simplified - using returns from equity curve)
        sharpe_ratio = self._calculate_sharpe_ratio()
        
        # Drawdown
        max_drawdown, max_drawdown_pct = self._calculate_drawdown()
        
        return PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            total_pnl=total_pnl,
            total_return=total_return,
            total_return_pct=total_return_pct,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            initial_capital=self.initial_capital,
            final_capital=self.current_capital
        )
    
    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.0) -> float:
        """Calculate Sharpe ratio from equity curve.
        
        Args:
            risk_free_rate: Risk-free rate (annual, as decimal, e.g., 0.02 for 2%)
        
        Returns:
            Sharpe ratio
        """
        if len(self.equity_curve) < 2:
            return 0.0
        
        # Calculate returns
        returns = []
        for i in range(1, len(self.equity_curve)):
            prev_value = self.equity_curve[i-1][1]
            curr_value = self.equity_curve[i][1]
            if prev_value > 0:
                ret = (curr_value - prev_value) / prev_value
                returns.append(ret)
        
        if not returns:
            return 0.0
        
        # Calculate mean and std of returns
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_return = math.sqrt(variance) if variance > 0 else 0.0
        
        if std_return == 0:
            return 0.0
        
        # Annualize (assuming daily returns - adjust as needed)
        # For simplicity, we'll use the period returns directly
        sharpe = (mean_return - risk_free_rate / 252) / std_return if std_return > 0 else 0.0
        
        return sharpe
    
    def _calculate_drawdown(self) -> tuple[float, float]:
        """Calculate maximum drawdown.
        
        Returns:
            (max_drawdown, max_drawdown_pct) tuple
        """
        if not self.equity_curve:
            return (0.0, 0.0)
        
        peak = self.initial_capital
        max_drawdown = 0.0
        max_drawdown_pct = 0.0
        
        for _, value in self.equity_curve:
            if value > peak:
                peak = value
            
            drawdown = peak - value
            drawdown_pct = (drawdown / peak * 100) if peak > 0 else 0.0
            
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_pct = drawdown_pct
        
        return (max_drawdown, max_drawdown_pct)
    
    def get_equity_curve_data(self) -> tuple[List[datetime], List[float]]:
        """Get equity curve data for plotting.
        
        Returns:
            (timestamps, values) tuple
        """
        if not self.equity_curve:
            return ([], [])
        
        timestamps = [t for t, _ in self.equity_curve]
        values = [v for _, v in self.equity_curve]
        return (timestamps, values)
    
    def get_trade_history(self) -> List[Trade]:
        """Get all recorded trades."""
        return self.trades.copy()
    
    def get_open_positions(self) -> Dict[str, Position]:
        """Get current open positions."""
        return self.positions.copy()
    
    def reset(self):
        """Reset tracker (for new backtest run)."""
        self.trades.clear()
        self.equity_curve.clear()
        self.positions.clear()
        self.closed_pnls.clear()
        self.current_prices.clear()
        self.current_capital = self.initial_capital

