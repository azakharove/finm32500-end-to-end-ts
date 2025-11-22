from abc import ABC, abstractmethod

from trading_lib.models import MarketDataPoint

class Strategy(ABC):
    """Base class for trading strategies.

    Enforces a common interface for trading strategies by defining methods
    that all subclasses must implement.
    """

    def __init__(self, quantity: int = 100):
        super().__init__()
        self._prices = [] 
        self.quantity = quantity 

    @abstractmethod
    def generate_signals(self, tick: MarketDataPoint) -> list[tuple]:
        raise NotImplementedError("Subclasses must implement generate_signals method")