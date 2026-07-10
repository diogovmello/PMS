from datetime import date

import pandas as pd
import pytest

from core.products.option import Option
from core.risk.greeks import (
    black_scholes_delta,
    time_to_expiry_years,
    compute_option_delta,
)
from core.risk import greeks as greeks_module


class TestBlackScholesDelta:
    def test_call_delta_in_zero_one_range(self):
        delta = black_scholes_delta(
            underlying_price=100, strike=100, time_to_expiry=0.5, volatility=0.3, option_type="call",
        )
        assert 0 < delta < 1

    def test_put_delta_in_minus_one_zero_range(self):
        delta = black_scholes_delta(
            underlying_price=100, strike=100, time_to_expiry=0.5, volatility=0.3, option_type="put",
        )
        assert -1 < delta < 0

    def test_deep_itm_call_delta_near_one(self):
        delta = black_scholes_delta(
            underlying_price=300, strike=50, time_to_expiry=0.5, volatility=0.2, option_type="call",
        )
        assert delta == pytest.approx(1, abs=1e-3)

    def test_deep_otm_call_delta_near_zero(self):
        delta = black_scholes_delta(
            underlying_price=50, strike=300, time_to_expiry=0.5, volatility=0.2, option_type="call",
        )
        assert delta == pytest.approx(0, abs=1e-3)

    def test_call_and_put_delta_differ_by_exactly_one(self):
        params = dict(underlying_price=105, strike=100, time_to_expiry=0.25, volatility=0.35)
        call_delta = black_scholes_delta(option_type="call", **params)
        put_delta = black_scholes_delta(option_type="put", **params)
        assert call_delta - put_delta == pytest.approx(1)

    def test_expired_option_raises(self):
        with pytest.raises(ValueError):
            black_scholes_delta(
                underlying_price=100, strike=100, time_to_expiry=0, volatility=0.3, option_type="call",
            )

    def test_negative_time_to_expiry_raises(self):
        with pytest.raises(ValueError):
            black_scholes_delta(
                underlying_price=100, strike=100, time_to_expiry=-0.01, volatility=0.3, option_type="call",
            )

    def test_unknown_option_type_raises(self):
        with pytest.raises(ValueError):
            black_scholes_delta(
                underlying_price=100, strike=100, time_to_expiry=0.5, volatility=0.3, option_type="straddle",
            )


class TestTimeToExpiryYears:
    def test_computes_fraction_of_year_remaining(self):
        t = time_to_expiry_years("2026-07-19", as_of=date(2026, 7, 9))
        assert t == pytest.approx(10 / 365)

    def test_past_expiry_is_negative(self):
        t = time_to_expiry_years("2026-07-01", as_of=date(2026, 7, 9))
        assert t < 0


class TestComputeOptionDelta:
    def test_wires_volatility_and_time_to_expiry_together(self, monkeypatch):
        history = pd.Series([300.0, 302.0, 298.0, 305.0, 303.0, 307.0])

        class _FakeDownloadResult:
            def __init__(self, close):
                self._close = close

            def __getitem__(self, key):
                return self._close

        def _fake_download(symbol, period, progress, threads):
            return _FakeDownloadResult(history)

        monkeypatch.setattr(greeks_module.yf, "download", _fake_download)

        option = Option("AAPL271231C00300000", strike=300, expiry="2027-12-31",
                         option_type="call", underlying="AAPL")

        delta = compute_option_delta(option, underlying_price=310)
        assert 0 <= delta <= 1
