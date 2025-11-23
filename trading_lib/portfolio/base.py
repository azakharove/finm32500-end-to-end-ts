from abc import ABC, abstractmethod

from trading_lib.models import MarketDataPoint, Order

class Portfolio(ABC):
    """
    Portfolio management base class for tracking cash and holdings.

    Enforces a common interface for portfolios by defining methods
    that all subclasses must implement.

    Holdings are stored as {'SYMBOL': {'quantity': int, 'avg_price': float}}
    """

    def __init__(self):
        super().__init__()

    @abstractmethod
    def update_cash(self, amount: float):
        raise NotImplementedError("Subclasses must implement update_cash method")
    
    @abstractmethod
    def add_to_holding(self, symbol: str, quantity: int, price: float):
        raise NotImplementedError("Subclasses must implement add_to_holding method")
    
    @abstractmethod
    def apply_order(self, order: Order):
        raise NotImplementedError("Subclasses must implement apply_order method")

    @abstractmethod
    def get_holding(self, symbol: str):
        raise NotImplementedError("Subclasses must implement get_holding method")
    
    @abstractmethod
    def get_all_holdings(self):
        raise NotImplementedError("Subclasses must implement get_all_holdings method")
    
    def sync_state(self, cash: float, positions: dict):
        """Sync portfolio state with external source (optional to implement).
        
        Args:
            cash: Current cash balance
            positions: Dict of {symbol: {'quantity': int, 'avg_price': float}}
        """
        pass  # Optional - only needed for live trading