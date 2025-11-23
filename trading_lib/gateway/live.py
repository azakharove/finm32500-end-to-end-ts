"""Live Gateway for real-time trading with Alpaca."""

from trading_lib.gateway.base import Gateway
from trading_lib.models import MarketDataPoint, Order, OrderStatus


class LiveGateway(Gateway):
    """Gateway for live trading with Alpaca API."""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://paper-api.alpaca.markets",
        symbols: list = None,
        audit_log_path: str = None
    ):
        """Initialize live gateway.
        
        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            base_url: API base URL (paper or live trading)
            symbols: List of symbols to subscribe to
            audit_log_path: Optional path for order audit log
        """
        super().__init__(audit_log_path=audit_log_path)
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.symbols = symbols or []
        self._api = None
        self._connected = False
    
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
        print(f"Connected to Alpaca (Paper: {self.base_url})")
        print(f"Account Status: {account.status}")
        print(f"Buying Power: ${float(account.buying_power):.2f}")
        
        self._connected = True
    
    def disconnect(self):
        """Disconnect from Alpaca."""
        self._close_audit_log()
        self._connected = False
        print("Disconnected from Alpaca")
    
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
            
            print(f"Submitted order to Alpaca: {alpaca_order.id}")
            
            # Log order submission
            self.log_order_sent(order, order_id=alpaca_order.id)
            
            # Update order status
            order.status = OrderStatus.PENDING
            self._publish_order_update(order)
            
        except Exception as e:
            print(f"Error submitting order: {e}")
            order.status = OrderStatus.FAILED
            self.log_order_cancelled(order, notes=str(e))
            self._publish_order_update(order)
    
    def run(self):
        """Stream real-time market data from Alpaca.
        
        Note: This is a simplified polling implementation.
        Production systems would use WebSocket streaming.
        """
        if not self._connected:
            self.connect()
        
        import time
        
        print(f"Streaming market data for: {', '.join(self.symbols)}")
        
        # Poll for latest trades (simplified - use WebSocket in production)
        while self._connected:
            for symbol in self.symbols:
                try:
                    trade = self._api.get_latest_trade(symbol)
                    data_point = MarketDataPoint(
                        timestamp=trade.timestamp,
                        symbol=symbol,
                        price=float(trade.price)
                    )
                    self._publish_market_data(data_point)
                except Exception as e:
                    print(f"Error fetching {symbol}: {e}")
            
            time.sleep(1)  # Poll every second

