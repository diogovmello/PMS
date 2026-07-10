from core.position import Portfolio
from core.risk.exposure import gross_exposure, net_exposure, exposure_by_symbol


def _portfolio_with_long_and_short():
    portfolio = Portfolio()
    portfolio.add_position("AAPL", 10, 100)   # long
    portfolio.add_position("TSLA", -5, 700)   # short
    return portfolio


def test_gross_exposure_sums_absolute_values():
    portfolio = _portfolio_with_long_and_short()
    prices = {"AAPL": 150, "TSLA": 750}
    # |10*150| + |-5*750| = 1500 + 3750
    assert gross_exposure(portfolio, prices) == 5250


def test_net_exposure_sums_signed_values():
    portfolio = _portfolio_with_long_and_short()
    prices = {"AAPL": 150, "TSLA": 750}
    # 10*150 + (-5*750) = 1500 - 3750
    assert net_exposure(portfolio, prices) == -2250


def test_exposure_by_symbol_breaks_out_each_position():
    portfolio = _portfolio_with_long_and_short()
    prices = {"AAPL": 150, "TSLA": 750}
    assert exposure_by_symbol(portfolio, prices) == {"AAPL": 1500, "TSLA": -3750}
