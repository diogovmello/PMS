import pytest

from core.loaders.order_based_loader import _apply_fill, OrderBasedPositionLoader
from core.orders.order import Order
from core.orders.repository import insert_order


class TestApplyFill:
    def test_open_long_from_flat(self):
        assert _apply_fill(0, 0.0, "buy", 10, 100) == (10, 100)

    def test_add_to_long_blends_average(self):
        net_qty, avg_price = _apply_fill(10, 100, "buy", 10, 200)
        assert net_qty == 20
        assert avg_price == pytest.approx(150)

    def test_partial_reduce_long_keeps_average(self):
        net_qty, avg_price = _apply_fill(20, 150, "sell", 5, 300)
        assert net_qty == 15
        assert avg_price == pytest.approx(150)

    def test_full_close_long_resets_average_to_zero(self):
        net_qty, avg_price = _apply_fill(15, 150, "sell", 15, 300)
        assert net_qty == 0
        assert avg_price == 0.0

    def test_flip_long_to_short_resets_average_to_fill_price(self):
        net_qty, avg_price = _apply_fill(10, 100, "sell", 15, 50)
        assert net_qty == -5
        assert avg_price == 50

    def test_open_short_from_flat(self):
        assert _apply_fill(0, 0.0, "sell", 10, 100) == (-10, 100)

    def test_add_to_short_blends_average(self):
        net_qty, avg_price = _apply_fill(-10, 100, "sell", 10, 200)
        assert net_qty == -20
        assert avg_price == pytest.approx(150)

    def test_partial_reduce_short_keeps_average(self):
        net_qty, avg_price = _apply_fill(-20, 150, "buy", 5, 300)
        assert net_qty == -15
        assert avg_price == pytest.approx(150)

    def test_flip_short_to_long_resets_average_to_fill_price(self):
        net_qty, avg_price = _apply_fill(-5, 50, "buy", 15, 80)
        assert net_qty == 10
        assert avg_price == 80


class TestOrderBasedPositionLoader:
    def test_replays_fills_into_blended_position(self, temp_orders_db):
        insert_order(Order(pm="smith", symbol="AAPL", side="buy", quantity=10, price=100))
        insert_order(Order(pm="smith", symbol="AAPL", side="buy", quantity=10, price=200))

        portfolios = OrderBasedPositionLoader().load()
        pos = portfolios["smith"].positions["AAPL"]

        assert pos.quantity == 20
        assert pos.entry_price == pytest.approx(150)

    def test_fully_closed_position_is_dropped(self, temp_orders_db):
        insert_order(Order(pm="jones", symbol="TSLA", side="buy", quantity=20, price=700))
        insert_order(Order(pm="jones", symbol="TSLA", side="sell", quantity=20, price=750))

        portfolios = OrderBasedPositionLoader().load()

        assert "jones" not in portfolios or "TSLA" not in portfolios["jones"].positions

    def test_ignores_non_filled_orders(self, temp_orders_db):
        insert_order(Order(pm="smith", symbol="AAPL", side="buy", quantity=10, price=100))
        insert_order(Order(pm="smith", symbol="AAPL", side="buy", quantity=10, price=999, status="CANCELLED"))

        portfolios = OrderBasedPositionLoader().load()
        pos = portfolios["smith"].positions["AAPL"]

        assert pos.quantity == 10
        assert pos.entry_price == pytest.approx(100)

    def test_carries_instrument_metadata_from_last_fill(self, temp_orders_db):
        insert_order(Order(
            pm="smith", symbol="ES=F", side="buy", quantity=2, price=5000,
            product_type="future", multiplier=50,
        ))

        portfolios = OrderBasedPositionLoader().load()
        instrument = portfolios["smith"].positions["ES=F"].instrument

        assert instrument.multiplier == 50
