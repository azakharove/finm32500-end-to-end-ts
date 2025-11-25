"""Live Gateway for real-time trading with Alpaca."""

from trading_lib.gateway.base import Gateway
from trading_lib.models import (
    MarketDataPoint, Order, OrderStatus,
    AlpacaPosition, AlpacaOrder, AccountState
)
from trading_lib.logging_config import get_logger
from trading_lib.market_data_logger import MarketDataLogger


class LiveGateway(Gateway):
    """Gateway for live trading with Alpaca API."""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://paper-api.alpaca.markets",
        symbols: list = None,
        audit_log_path: str = None,
        save_market_data: bool = True,
        market_data_dir: str = "data/live"
    ):
        """Initialize live gateway.
        
        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            base_url: API base URL (paper or live trading)
            symbols: List of symbols to subscribe to
            audit_log_path: Optional path for order audit log
            save_market_data: Whether to save market data to CSV (default: True)
            market_data_dir: Directory to save market data CSVs
        """
        super().__init__(audit_log_path=audit_log_path)
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.symbols = symbols or []
        self._api = None
        self._connected = False
        self.logger = get_logger('gateway.live')
        
        # Market data logging
        self.save_market_data = save_market_data
        self.market_data_logger = MarketDataLogger(market_data_dir) if save_market_data else None
    
    def connect(self):
        """Connect to Alpaca API."""
        try:
            import alpaca_trade_api as tradeapi
        except ImportError:
            raise ImportError(
                "alpaca-trade-api required for live trading. "
                "Install with: pip install alpaca-trade-api"
            )
        
        self._api = tradeapi.REST(self.api_key, self.api_secret, self.base_url)
        
        # Test connection
        account = self._api.get_account()
        self.logger.info(f"Connected to Alpaca: {self.base_url}")
        self.logger.info(f"Account Status: {account.status}")
        self.logger.info(f"Buying Power: ${float(account.buying_power):,.2f}")
        self.logger.info(f"Portfolio Value: ${float(account.portfolio_value):,.2f}")
        
        self._connected = True
    
    def get_account_state(self) -> AccountState:
        """Get current account state from Alpaca.
        
        Returns:
            AccountState: Structured account state with positions and orders
        """
        if not self._connected:
            raise RuntimeError("Gateway not connected")
        
        # Get account info
        account = self._api.get_account()
        
        # Get current positions
        positions_raw = self._api.list_positions()
        positions_dict = {}
        for pos in positions_raw:
            alpaca_pos = AlpacaPosition.from_alpaca_position(pos)
            positions_dict[alpaca_pos.symbol] = alpaca_pos
        
        # Get open orders
        open_orders_raw = self._api.list_orders(status='open')
        orders_list = [AlpacaOrder.from_alpaca_order(order) for order in open_orders_raw]
        
        state = AccountState(
            cash=float(account.cash),
            buying_power=float(account.buying_power),
            portfolio_value=float(account.portfolio_value),
            positions=positions_dict,
            open_orders=orders_list
        )
        
        self.logger.info(f"Retrieved account state: {len(positions_dict)} positions, {len(orders_list)} open orders")
        
        return state
    
    def disconnect(self):
        """Disconnect from Alpaca."""
        self._close_audit_log()
        if self.market_data_logger:
            self.market_data_logger.close_all()
        self._connected = False
        self.logger.info("Disconnected from Alpaca")
    
    def submit_order(self, order: Order):
        """Submit order to Alpaca.
        
        Args:
            order: Order to submit
        """
        if not self._connected:
            raise RuntimeError("Gateway not connected")
        
        try:
            # Determine side
            side = 'buy' if order.quantity > 0 else 'sell'
            qty = abs(order.quantity)
            
            # Submit to Alpaca
            alpaca_order = self._api.submit_order(
                symbol=order.symbol,
                qty=qty,
                side=side,
                type='limit',
                limit_price=order.price,
                time_in_force='day'
            )
            
            self.logger.info(f"Submitted order to Alpaca: {alpaca_order.id}")
            
            # Log order submission
            self.log_order_sent(order, order_id=alpaca_order.id)
            
            # Update order status to ACTIVE
            # Note: filled_quantity will be updated when polling for order status
            order.status = OrderStatus.ACTIVE
            order.filled_quantity = 0  # Initialize
            self._publish_order_update(order)
            
        except Exception as e:
            self.logger.error(f"Error submitting order: {e}")
            order.status = OrderStatus.FAILED
            self.log_order_cancelled(order, notes=str(e))
            self._publish_order_update(order)
    
    def run(self):
        """Stream real-time market data from Alpaca.
        
        Note: This is a simplified polling implementation.
        """
        if not self._connected:
            self.connect()
        
        import time
        
        self.logger.info(f"Streaming market data for: {', '.join(self.symbols)}")
        
        try:
            # Poll for latest trades 
            while self._connected:
                for symbol in self.symbols:
                    try:
                        trade = self._api.get_latest_trade(symbol)
                        data_point = MarketDataPoint(
                            timestamp=trade.timestamp,
                            symbol=symbol,
                            price=float(trade.price)
                        )
                        # Publish to subscribers
                        self._publish_market_data(data_point)
                        
                        # Save to CSV if enabled
                        if self.market_data_logger:
                            self.market_data_logger.log_tick(data_point)
                    except Exception as e:
                        self.logger.error(f"Error fetching {symbol}: {e}")
                
                time.sleep(1)  # Poll every second
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, stopping...")
            raise

