from trading_lib.matching_engine import MatchingEngine
from trading_lib.models import Order, OrderStatus

def test_submitting_order_with_id():
    engine = MatchingEngine(cancel_rate=0.0, partial_fill_rate=0.0)
    order = Order(symbol="AAPL", quantity=10, price=150, status=OrderStatus.PENDING, id="custom_id_123")
    
    def assert_order_atrb(ord: Order):
        assert ord.id == "custom_id_123"
        assert ord.status == OrderStatus.FILLED
        assert ord.filled_quantity == 10
    
    engine.subscribe_order_updates(assert_order_atrb)
    
    processed_order = engine.process_order(order)
    assert_order_atrb(processed_order)

def test_submitting_order_without_id():
    engine = MatchingEngine(cancel_rate=0.0, partial_fill_rate=0.0)
    order = Order(symbol="AAPL", quantity=10, price=150, status=OrderStatus.PENDING)
    
    def assert_order_atrb(ord: Order):
        assert ord.id is not None
        assert ord.status == OrderStatus.FILLED
        assert ord.filled_quantity == 10
    
    engine.subscribe_order_updates(assert_order_atrb)
    
    processed_order = engine.process_order(order)
    assert_order_atrb(processed_order)

def test_partially_filled_order():
    engine = MatchingEngine(cancel_rate=0.0, partial_fill_rate=1.0)  # Force partial fill
    order = Order(symbol="AAPL", quantity=9, price=150, status=OrderStatus.PENDING)
    
    def assert_order_atrb(ord: Order):
        assert ord.id is not None
        assert ord.status == OrderStatus.PARTIALLY_FILLED
        assert ord.filled_quantity == 3  # 1/3 of 9 is 3
    
    engine.subscribe_order_updates(assert_order_atrb)
    
    processed_order = engine.process_order(order)
    assert_order_atrb(processed_order)

def test_cancelled_order():
    engine = MatchingEngine(cancel_rate=1.0, partial_fill_rate=0.0)  # Force cancel
    order = Order(symbol="AAPL", quantity=10, price=150, status=OrderStatus.PENDING)
    
    def assert_order_atrb(ord: Order):
        assert ord.id is not None
        assert ord.status == OrderStatus.CANCELED
        assert ord.filled_quantity == 0
    
    engine.subscribe_order_updates(assert_order_atrb)
    
    processed_order = engine.process_order(order)
    assert_order_atrb(processed_order)

def test_fully_filled_order():
    engine = MatchingEngine(cancel_rate=0.0, partial_fill_rate=0.0)  # Force full fill
    order = Order(symbol="AAPL", quantity=15, price=150, status=OrderStatus.PENDING)
    
    def assert_order_atrb(ord: Order):
        assert ord.id is not None
        assert ord.status == OrderStatus.FILLED
        assert ord.filled_quantity == 15
    
    engine.subscribe_order_updates(assert_order_atrb)
    
    processed_order = engine.process_order(order)
    assert_order_atrb(processed_order)