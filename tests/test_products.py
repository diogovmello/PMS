import pytest

from core.products.equity import Equity
from core.products.future import Future
from core.products.option import Option
from core.products.perpetual import Perpetual
from core.products.factory import build_instrument


class TestEquity:
    def test_market_value(self):
        eq = Equity("AAPL")
        assert eq.market_value(quantity=10, current_price=150) == 1500

    def test_unrealized_pnl_long(self):
        eq = Equity("AAPL")
        assert eq.unrealized_pnl(quantity=10, entry_price=100, current_price=150) == 500

    def test_unrealized_pnl_short(self):
        eq = Equity("AAPL")
        assert eq.unrealized_pnl(quantity=-10, entry_price=150, current_price=100) == 500


class TestFuture:
    def test_market_value_scaled_by_multiplier(self):
        fut = Future("ES=F", multiplier=50)
        assert fut.market_value(quantity=2, current_price=5000) == 500000

    def test_unrealized_pnl_scaled_by_multiplier(self):
        fut = Future("ES=F", multiplier=50)
        assert fut.unrealized_pnl(quantity=2, entry_price=4900, current_price=5000) == 10000


class TestPerpetual:
    def test_market_value_scaled_by_multiplier(self):
        perp = Perpetual("BTCUSDT", multiplier=1)
        assert perp.market_value(quantity=2, current_price=65000) == 130000

    def test_unrealized_pnl_scaled_by_multiplier(self):
        perp = Perpetual("BTCUSDT", multiplier=1)
        assert perp.unrealized_pnl(quantity=2, entry_price=64000, current_price=65000) == 2000

    def test_unrealized_pnl_short(self):
        perp = Perpetual("BTCUSDT", multiplier=1)
        assert perp.unrealized_pnl(quantity=-2, entry_price=65000, current_price=64000) == 2000


class TestOption:
    def test_market_value_scaled_by_multiplier(self):
        opt = Option("AAPL260717C00300000", strike=300, expiry="2026-07-17",
                      option_type="call", underlying="AAPL", multiplier=100)
        assert opt.market_value(quantity=5, current_price=15) == 7500

    def test_unrealized_pnl_scaled_by_multiplier(self):
        opt = Option("AAPL260717C00300000", strike=300, expiry="2026-07-17",
                      option_type="call", underlying="AAPL", multiplier=100)
        assert opt.unrealized_pnl(quantity=5, entry_price=8.5, current_price=15) == pytest.approx(3250)

    def test_option_type_lowercased(self):
        opt = Option("AAPL260717P00300000", strike=300, expiry="2026-07-17",
                      option_type="PUT", underlying="AAPL")
        assert opt.option_type == "put"


class TestBuildInstrument:
    def test_defaults_to_equity(self):
        instrument = build_instrument("AAPL")
        assert isinstance(instrument, Equity)

    def test_builds_future_with_multiplier(self):
        instrument = build_instrument("ES=F", product_type="future", multiplier=50)
        assert isinstance(instrument, Future)
        assert instrument.multiplier == 50

    def test_future_multiplier_defaults_to_one(self):
        instrument = build_instrument("ES=F", product_type="future")
        assert instrument.multiplier == 1

    def test_builds_perpetual_with_multiplier(self):
        instrument = build_instrument("BTCUSDT", product_type="perpetual", multiplier=1)
        assert isinstance(instrument, Perpetual)
        assert instrument.multiplier == 1

    def test_perpetual_multiplier_defaults_to_one(self):
        instrument = build_instrument("BTCUSDT", product_type="perpetual")
        assert instrument.multiplier == 1

    def test_builds_option_with_fields(self):
        instrument = build_instrument(
            "AAPL260717C00300000", product_type="option",
            strike=300, expiry="2026-07-17", option_type="call", underlying="AAPL",
        )
        assert isinstance(instrument, Option)
        assert instrument.strike == 300
        assert instrument.underlying == "AAPL"
        assert instrument.multiplier == 100

    def test_unknown_product_type_raises(self):
        with pytest.raises(ValueError):
            build_instrument("AAPL", product_type="bond")
