import pytest

from core.prices import binance_perp_provider as binance_module
from core.prices.binance_perp_provider import BinancePerpPriceProvider

_PAYLOAD = [
    {"symbol": "BTCUSDT", "markPrice": "65000.50", "lastFundingRate": "0.00010000"},
    {"symbol": "ETHUSDT", "markPrice": "3400.25", "lastFundingRate": "-0.00005000"},
]


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


@pytest.fixture
def provider(monkeypatch):
    def _fake_get(url, timeout):
        return _FakeResponse(_PAYLOAD)

    monkeypatch.setattr(binance_module.requests, "get", _fake_get)
    return BinancePerpPriceProvider()


class TestGetPrices:
    def test_returns_mark_price_as_float(self, provider):
        prices = provider.get_prices(["BTCUSDT", "ETHUSDT"])
        assert prices == {"BTCUSDT": 65000.50, "ETHUSDT": 3400.25}

    def test_missing_symbol_raises(self, provider):
        with pytest.raises(ValueError):
            provider.get_prices(["BTCUSDT", "DOGEUSDT"])


class TestGetFundingRates:
    def test_returns_funding_rate_as_float(self, provider):
        rates = provider.get_funding_rates(["BTCUSDT", "ETHUSDT"])
        assert rates == {"BTCUSDT": 0.0001, "ETHUSDT": -0.00005}
