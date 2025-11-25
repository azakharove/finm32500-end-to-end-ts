from trading_lib.matching_engine import MatchingEngine
from trading_lib.models import Order, OrderStatus

def test_submitting_order_with_id():
    engine = MatchingEngine(cancel_rate=0.0, partial_fill_rate=0.0)
    order = Order(symbol="AAPL", quantity=10, price=150, status=OrderStatus.PENDING, id="custom_id_123")
    
    def assert_order_atrb(ord: Order):
        assert ord.id == "custom_id_123"
        assert ord.status == OrderStatus.FILLED
    
    engine.subscribe_order_updates(lambda ord: print(f"Order {ord.id} Update: {ord.status}"))
    engine.subscribe_order_updates(assert_order_atrb)
    
    processed_order = engine.process_order(order)
    assert_order_atrb(processed_order)