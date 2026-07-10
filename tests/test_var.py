import pandas as pd
import pytest

from core.position import Portfolio
from core.products.equity import Equity
from core.products.option import Option
from core.risk import var as var_module


class _FakeDownloadResult:
    """Mimics yf.download(...)['Close'] indexing without hitting the network."""

    def __init__(self, close):
        self._close = close

    def __getitem__(self, key):
        assert key == "Close"
        return self._close


def _make_fake_download(price_series_by_symbol):
    call_log = []

    def _fake_download(symbols, period, progress, threads):
        call_log.append(list(symbols))
        if len(symbols) == 1:
            close = price_series_by_symbol[symbols[0]]  # bare Series, like real yfinance for one ticker
        else:
            close = pd.DataFrame({s: price_series_by_symbol[s] for s in symbols})
        return _FakeDownloadResult(close)

    _fake_download.call_log = call_log
    return _fake_download


def test_var_matches_manual_calculation_for_single_position(monkeypatch):
    history = pd.Series([100.0, 102.0, 101.0, 103.0, 102.5])
    fake_download = _make_fake_download({"AAPL": history})
    monkeypatch.setattr(var_module.yf, "download", fake_download)

    portfolio = Portfolio()
    portfolio.add_position("AAPL", 10, 90, Equity("AAPL"))

    result = var_module.compute_portfolio_var(portfolio, {"AAPL": 105}, confidence=0.95)

    exposure = 10 * 105
    expected_std = history.pct_change().std()
    expected = 1.645 * abs(exposure) * expected_std
    assert result == pytest.approx(expected)
    assert fake_download.call_log == [["AAPL"]]


def test_var_uses_underlying_returns_for_option_positions(monkeypatch):
    history = pd.Series([300.0, 305.0, 302.0, 310.0, 308.0])
    fake_download = _make_fake_download({"AAPL": history})
    monkeypatch.setattr(var_module.yf, "download", fake_download)

    portfolio = Portfolio()
    option = Option("AAPL260717C00300000", strike=300, expiry="2026-07-17",
                     option_type="call", underlying="AAPL")
    portfolio.add_position("AAPL260717C00300000", 5, 8.5, option)

    result = var_module.compute_portfolio_var(portfolio, {"AAPL260717C00300000": 15})

    # dedup'd down to the underlying's symbol, not the OCC contract symbol
    assert fake_download.call_log == [["AAPL"]]
    assert result > 0


def test_var_dedupes_fetch_for_equity_and_option_on_same_underlying(monkeypatch):
    history = pd.Series([300.0, 305.0, 302.0, 310.0, 308.0])
    fake_download = _make_fake_download({"AAPL": history})
    monkeypatch.setattr(var_module.yf, "download", fake_download)

    portfolio = Portfolio()
    portfolio.add_position("AAPL", 10, 290, Equity("AAPL"))
    option = Option("AAPL260717C00300000", strike=300, expiry="2026-07-17",
                     option_type="call", underlying="AAPL")
    portfolio.add_position("AAPL260717C00300000", 5, 8.5, option)

    result = var_module.compute_portfolio_var(
        portfolio, {"AAPL": 308, "AAPL260717C00300000": 15}
    )

    assert fake_download.call_log == [["AAPL"]]  # one fetch, not two
    assert result > 0


def test_unsupported_confidence_raises():
    portfolio = Portfolio()
    portfolio.add_position("AAPL", 10, 90)
    with pytest.raises(ValueError):
        var_module.compute_portfolio_var(portfolio, {"AAPL": 100}, confidence=0.90)
