import random
from datetime import datetime
from typing import List, Tuple, Optional, Iterable

from trading_lib.models import Action, MarketDataPoint, Order, OrderStatus, RecordingInterval
from trading_lib.portfolio import Portfolio
from trading_lib.strategy import Strategy
from trading_lib.exceptions import ExecutionError, OrderError


class ExecutionEngine:
    """Executes trading strategies by processing market data and managing orders.

    Processing flow:
    1. Iterate through MarketDataPoint objects in timestamp order
    2. For each tick, invoke strategies to generate signals
    3. Instantiate and validate Order objects from signals
    4. Execute orders by updating the portfolio
    """

    def __init__(
        self, 
        strategy: Strategy, 
        portfolio: Portfolio, 
        failure_rate: float = 0.0, 
        recording_interval: RecordingInterval = RecordingInterval.SECOND
    ):
        self.strategy = strategy
        self.portfolio = portfolio
        self.failure_rate = failure_rate  # Simulate 5% failure rate by default
        self.recording_interval = recording_interval
        self.portfolio_history: List[Tuple[datetime, float, float]] = []
        self.last_recorded_period: Optional[tuple] = None
        self.current_prices: dict[str, float] = {}

    def record_portfolio_value(self, timestamp: datetime, cash: float, holdings: float):
        self.portfolio_history.append((timestamp, cash, holdings))
    
    def _get_period(self, timestamp: datetime) -> tuple:
        """Extract period identifier from timestamp based on recording_interval."""
        match self.recording_interval:
            case RecordingInterval.TICK:
                return (timestamp,)  # Every single tick
            case RecordingInterval.SECOND:
                return (timestamp.year, timestamp.month, timestamp.day, timestamp.hour, timestamp.minute, timestamp.second)
            case RecordingInterval.MINUTE:
                return (timestamp.year, timestamp.month, timestamp.day, timestamp.hour, timestamp.minute)
            case RecordingInterval.HOURLY:
                return (timestamp.year, timestamp.month, timestamp.day, timestamp.hour)
            case RecordingInterval.DAILY:
                return (timestamp.year, timestamp.month, timestamp.day)
            case RecordingInterval.WEEKLY:
                return (timestamp.year, timestamp.isocalendar()[1])  # ISO week number
            case RecordingInterval.MONTHLY:
                return (timestamp.year, timestamp.month)
            case _:
                raise ValueError(f"Unknown recording interval: {self.recording_interval}")
    
    def process_tick(self, tick: MarketDataPoint):
        try:
            signals = self.strategy.generate_signals(tick)
            self.current_prices[tick.symbol] = tick.price
            for symbol, quantity, price, action in signals:
                if action != Action.HOLD:
                    order = Order(
                        symbol,
                        quantity,
                        price,
                        status=OrderStatus.PENDING,
                    )
                    self.execute_order(order)
        except Exception as e:
            print(f"Error processing tick {tick} with strategy {self.strategy}: {e}")

    def process_ticks(self, ticks: Iterable[MarketDataPoint]):
    
        # use a generator to process ticks in order
        for tick in ticks:
            self.process_tick(tick)
            
            # Determine current period
            current_period = self._get_period(tick.timestamp)
            
            # Record portfolio value when period changes
            if self.last_recorded_period is None or current_period != self.last_recorded_period:
                self.record_portfolio_value(tick.timestamp, self.portfolio.get_cash(), self.portfolio.get_holdings_value(self.current_prices))
                self.last_recorded_period = current_period

    def execute_order(self, order: Order):
        try:
            # Validate order status
            if order.status != OrderStatus.PENDING:
                raise OrderError(order, "Order must be PENDING to execute")

            # Check if portfolio can execute this order (sufficient cash/holdings)
            if not self.portfolio.can_execute_order(order):
                reason = "Insufficient cash" if order.quantity > 0 else "Insufficient holdings"
                raise OrderError(order, reason)

            # Simulate occasional execution failures 
            if self.failure_rate > 0 and random.random() < self.failure_rate:
                raise ExecutionError(order, "Simulated execution failure")

            # Execute order
            order.status = OrderStatus.COMPLETED
            self.portfolio.apply_order(order)
            print(
                f"Executed order: {order.symbol}, Quantity: {order.quantity}, Price: {order.price}, Status: {order.status}"
            )

        except ExecutionError as e:
            # Log execution failures but continue processing
            print(e)
            order.status = OrderStatus.FAILED

        except OrderError as e:
            print(e)
            order.status = OrderStatus.FAILED

    def get_portfolio_history(self):
        return self.portfolio_history
    
    def get_current_prices(self):
        return self.current_prices
    
    def record_final_state(self, final_timestamp: datetime):
        """Record the final portfolio state after all ticks are processed."""
        holdings_value = self.portfolio.get_holdings_value(self.current_prices)
        self.record_portfolio_value(final_timestamp, self.portfolio.get_cash(), holdings_value)