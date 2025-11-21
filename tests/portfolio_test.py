import pytest

from trading_lib.portfolio import Portfolio
from trading_lib.models import Order, OrderStatus
from trading_lib.exceptions import OrderError


def test_update_cash():
    portfolio = Portfolio()
    
    portfolio.update_cash(10000)
    assert portfolio.cash == 10000

    portfolio.update_cash(-3000)
    assert portfolio.cash == 7000

    with pytest.raises(ValueError):
        portfolio.update_cash(-10000)

def test_add_to_holding():
    portfolio = Portfolio(cash=10000)
    
    portfolio.add_to_holding("AAPL", 10, 150)
    assert portfolio.get_holding("AAPL") == {"quantity": 10, "avg_price": 150.0}
    
    portfolio.add_to_holding("AAPL", 30, 100)
    assert portfolio.get_holding("AAPL") == {"quantity": 40, "avg_price": 112.5}
    
    portfolio.add_to_holding("AAPL", -20, 200)
    assert portfolio.get_holding("AAPL") == {"quantity": 20, "avg_price": 112.5}

def test_get_all_holdings():
    portfolio = Portfolio()
    
    portfolio.add_to_holding("AAPL", 10, 150)
    portfolio.add_to_holding("MSFT", 20, 200)
    
    assert portfolio.get_all_holdings() == {
        "AAPL": {"quantity": 10, "avg_price": 150.0},
        "MSFT": {"quantity": 20, "avg_price": 200.0},
    }

    portfolio.add_to_holding("AAPL", -10, 150)
    assert portfolio.get_all_holdings() == {
        "MSFT": {"quantity": 20, "avg_price": 200.0},
    }

def test_insufficient_holding():
    portfolio = Portfolio()
    portfolio.add_to_holding("AAPL", 10, 150)
    
    with pytest.raises(OrderError):
        portfolio.add_to_holding("AAPL", -15, 150)
    
def test_missing_holding():
    portfolio = Portfolio()
    assert portfolio.get_holding("MSFT") == {"quantity": 0, "avg_price": 0.0}

def test_zero_out_holding():
    portfolio = Portfolio()
    portfolio.add_to_holding("MSFT", 10, 150)
    portfolio.add_to_holding("MSFT", -10, 150)
    assert portfolio.get_holding("MSFT") == {"quantity": 0, "avg_price": 0.0}

def test_apply_order():
    portfolio = Portfolio(holdings={}, cash=10000)

    portfolio.apply_order(Order("AAPL", 10, 150, OrderStatus.COMPLETED))
    assert portfolio.cash == 8500
    assert portfolio.get_holding("AAPL") == {"quantity": 10, "avg_price": 150.0}

    portfolio.apply_order(Order("AAPL", 30, 100, OrderStatus.COMPLETED))
    assert portfolio.cash == 5500
    assert portfolio.get_holding("AAPL") == {"quantity": 40, "avg_price": 112.5}

    portfolio.apply_order(Order("AAPL", -20, 200, OrderStatus.COMPLETED))
    assert portfolio.cash == 9500
    assert portfolio.get_holding("AAPL") == {"quantity": 20, "avg_price": 112.5}

    # with self.assertRaises(ValueError):
    #     pending_order = Order("AAPL", 5, 180, OrderStatus.PENDING)
    #     portfolio.apply_order(pending_order)

    # with self.assertRaises(ValueError):
    #     over_sell_order = Order("AAPL", 20, 180, OrderStatus.COMPLETED)
    #     portfolio.apply_order(over_sell_order)


def test_apply_invalid_order():
    portfolio = Portfolio(cash=10000)
    with pytest.raises(OrderError):
        pending_order = Order("AAPL", 5, 180, OrderStatus.PENDING)
        portfolio.apply_order(pending_order)


def test_sell_quantity_exceeds_holding():
    portfolio = Portfolio(holdings={}, cash=10000)
    
    portfolio.apply_order(Order("AAPL", 10, 150, OrderStatus.COMPLETED))
    assert portfolio.cash == 8500
    assert portfolio.get_holding("AAPL") == {"quantity": 10, "avg_price": 150.0}
    with pytest.raises(OrderError):
        portfolio.apply_order(Order("AAPL", -15, 150, OrderStatus.COMPLETED))


def test_sell_missing_holding():
    portfolio = Portfolio(holdings={}, cash=10000)
    with pytest.raises(OrderError):
        portfolio.apply_order(Order("AAPL", -5, 150, OrderStatus.COMPLETED))


if __name__ == "__main__":
    test_insufficient_holding()