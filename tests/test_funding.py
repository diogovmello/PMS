import pytest

from core.position import Portfolio
from core.products.equity import Equity
from core.products.perpetual import Perpetual
from core.risk.funding import annualized_funding_yield, funding_pnl, portfolio_funding_pnl


class TestFundingPnl:
    def test_long_pays_when_funding_positive(self):
        portfolio = Portfolio()
        portfolio.add_position("BTCUSDT", quantity=2, entry_price=64000, instrument=Perpetual("BTCUSDT"))
        position = portfolio.get_position("BTCUSDT")

        pnl = funding_pnl(position, funding_rate=0.0001, current_price=65000)

        assert pnl == pytest.approx(-13.0)  # -(2 * 65000) * 0.0001

    def test_short_receives_when_funding_positive(self):
        portfolio = Portfolio()
        portfolio.add_position("BTCUSDT", quantity=-2, entry_price=64000, instrument=Perpetual("BTCUSDT"))
        position = portfolio.get_position("BTCUSDT")

        pnl = funding_pnl(position, funding_rate=0.0001, current_price=65000)

        assert pnl == pytest.approx(13.0)

    def test_long_receives_when_funding_negative(self):
        portfolio = Portfolio()
        portfolio.add_position("BTCUSDT", quantity=2, entry_price=64000, instrument=Perpetual("BTCUSDT"))
        position = portfolio.get_position("BTCUSDT")

        pnl = funding_pnl(position, funding_rate=-0.0002, current_price=65000)

        assert pnl == pytest.approx(26.0)


class TestPortfolioFundingPnl:
    def test_sums_only_perpetual_positions(self):
        portfolio = Portfolio()
        portfolio.add_position("BTCUSDT", quantity=2, entry_price=64000, instrument=Perpetual("BTCUSDT"))
        portfolio.add_position("ETHUSDT", quantity=-3, entry_price=3500, instrument=Perpetual("ETHUSDT"))
        portfolio.add_position("AAPL", quantity=10, entry_price=150, instrument=Equity("AAPL"))

        funding_rates = {"BTCUSDT": 0.0001, "ETHUSDT": 0.0001}
        prices = {"BTCUSDT": 65000, "ETHUSDT": 3400, "AAPL": 155}

        total = portfolio_funding_pnl(portfolio, funding_rates, prices)

        btc_pnl = -(2 * 65000) * 0.0001
        eth_pnl = -(-3 * 3400) * 0.0001
        assert total == pytest.approx(btc_pnl + eth_pnl)

    def test_empty_portfolio_is_zero(self):
        portfolio = Portfolio()
        assert portfolio_funding_pnl(portfolio, {}, {}) == 0.0


class TestAnnualizedFundingYield:
    def test_compounds_three_times_a_day_over_365_days(self):
        assert annualized_funding_yield(0.0001) == pytest.approx(0.0001 * 3 * 365)

    def test_negative_rate_stays_negative(self):
        assert annualized_funding_yield(-0.0001) < 0
