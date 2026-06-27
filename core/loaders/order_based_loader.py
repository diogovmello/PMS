from collections import defaultdict

from core.loaders.base import PositionLoader
from core.orders.repository import get_all_orders
from core.position import Portfolio
from core.products.factory import build_instrument


def _apply_fill(net_qty, avg_price, side, qty, price):
    """
    Average-cost accounting: adding to a position in the same direction
    blends price into the average. Reducing it leaves the average alone.
    Flipping direction resets the average to this fill's price.
    """
    signed_qty = qty if side == "buy" else -qty

    same_direction = net_qty == 0 or (net_qty > 0) == (signed_qty > 0)
    if same_direction:
        new_net_qty = net_qty + signed_qty
        new_avg_price = (abs(net_qty) * avg_price + qty * price) / abs(new_net_qty)
        return new_net_qty, new_avg_price

    new_net_qty = net_qty + signed_qty
    still_reducing = (net_qty > 0 and new_net_qty >= 0) or (net_qty < 0 and new_net_qty <= 0)
    if still_reducing:
        return new_net_qty, (avg_price if new_net_qty != 0 else 0.0)

    # Flipped from long to short or vice versa
    return new_net_qty, price


class OrderBasedPositionLoader(PositionLoader):
    """
    Builds positions by replaying every FILLED order per (pm, symbol) in
    timestamp order, instead of reading a static EOD snapshot. Instrument
    metadata (product_type, multiplier, strike, etc.) is assumed constant
    across fills of the same symbol, so it's just carried through rather
    than averaged.
    """

    def load(self):
        orders = sorted(
            (o for o in get_all_orders() if o.status == "FILLED"),
            key=lambda o: o.timestamp,
        )

        running = defaultdict(lambda: {"qty": 0.0, "avg_price": 0.0})
        instrument_info = {}

        for order in orders:
            key = (order.pm, order.symbol)
            state = running[key]
            state["qty"], state["avg_price"] = _apply_fill(
                state["qty"], state["avg_price"], order.side, order.quantity, order.price
            )
            instrument_info[key] = order

        portfolios = {}
        for key, state in running.items():
            if state["qty"] == 0:
                continue  # fully closed out, no open position
            pm, symbol = key
            order = instrument_info[key]
            instrument = build_instrument(
                symbol,
                product_type=order.product_type,
                multiplier=order.multiplier,
                strike=order.strike,
                expiry=order.expiry,
                option_type=order.option_type,
                underlying=order.underlying,
            )
            portfolios.setdefault(pm, Portfolio())
            portfolios[pm].add_position(symbol, state["qty"], state["avg_price"], instrument=instrument)

        return portfolios