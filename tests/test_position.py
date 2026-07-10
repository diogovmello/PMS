import pytest

from core.position import Position, Portfolio
from core.products.equity import Equity
from core.products.future import Future


def test_position_defaults_to_equity_instrument():
    pos = Position("AAPL", quantity=10, entry_price=100)
    assert isinstance(pos.instrument, Equity)


def test_position_market_value_and_pnl_delegate_to_instrument():
    pos = Position("ES=F", quantity=2, entry_price=4900, instrument=Future("ES=F", multiplier=50))
    assert pos.market_value(5000) == 500000
    assert pos.unrealized_pnl(5000) == 10000


def test_portfolio_add_and_get_position():
    portfolio = Portfolio()
    portfolio.add_position("AAPL", 10, 100)
    pos = portfolio.get_position("AAPL")
    assert pos.symbol == "AAPL"
    assert pos.quantity == 10


def test_portfolio_get_missing_position_returns_none():
    portfolio = Portfolio()
    assert portfolio.get_position("AAPL") is None


def test_portfolio_duplicate_symbol_raises():
    portfolio = Portfolio()
    portfolio.add_position("AAPL", 10, 100)
    with pytest.raises(ValueError):
        portfolio.add_position("AAPL", 5, 90)


def test_portfolio_totals_across_positions():
    portfolio = Portfolio()
    portfolio.add_position("AAPL", 10, 100)
    portfolio.add_position("MSFT", 5, 300)
    prices = {"AAPL": 150, "MSFT": 280}

    assert portfolio.total_market_value(prices) == 10 * 150 + 5 * 280
    assert portfolio.total_unrealized_pnl(prices) == 10 * (150 - 100) + 5 * (280 - 300)
