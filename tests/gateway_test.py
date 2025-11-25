from trading_lib.matching_engine import MatchingEngine
from trading_lib.models import Order, OrderStatus
from trading_lib.gateway.simulation import SimulationGateway

import pytest

def test_filling_order_with_id():
    engine = MatchingEngine(cancel_rate = 0.0, partial_fill_rate = 0.0)
    gateway = SimulationGateway(csv_path = "AAPL_5d_1m.csv", matching_engine = engine)
    
    def assert_order_atrb(ord: Order):
        assert ord.id == "custom_id_123"
        assert ord.status == OrderStatus.FILLED
        assert ord.filled_quantity == 10
    
    gateway.connect()
    
    gateway.subscribe_order_updates(assert_order_atrb)
    
    order = Order(symbol = "AAPL", quantity = 10, price = 150, status = OrderStatus.PENDING, id = "custom_id_123")

    gateway.submit_order(order)

def test_never_connected_gateway():
    engine = MatchingEngine(cancel_rate = 0.0, partial_fill_rate = 0.0)
    gateway = SimulationGateway(csv_path = "AAPL_5d_1m.csv", matching_engine = engine)
    
    order = Order(symbol = "AAPL", quantity = 10, price = 150, status = OrderStatus.PENDING)

    def assert_order_atrb(ord: Order):
        assert ord.id is not None

    gateway.subscribe_order_updates(assert_order_atrb)

    with pytest.raises(RuntimeError):
        gateway.submit_order(order)

def test_gateway_connect_disconnect():
    engine = MatchingEngine(cancel_rate = 0.0, partial_fill_rate = 0.0)
    gateway = SimulationGateway(csv_path = "AAPL_5d_1m.csv", matching_engine = engine)

    order = Order(symbol = "AAPL", quantity = 10, price = 150, status = OrderStatus.PENDING)
    
    def assert_order_atrb(ord: Order):
        assert ord.id is not None

    gateway.subscribe_order_updates(assert_order_atrb)

    with pytest.raises(RuntimeError):
        gateway.submit_order(order)

    gateway.connect()
    gateway.submit_order(order)
    
    gateway.disconnect()
    with pytest.raises(RuntimeError):
        gateway.submit_order(order)