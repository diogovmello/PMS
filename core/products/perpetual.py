from core.products.base import Instrument


class Perpetual(Instrument):
    """
    Perpetual futures contract (a "perp") - the dominant instrument on crypto
    derivatives venues. Unlike a dated Future, a perp never expires and never
    converges to spot at a settlement date; instead, longs and shorts
    exchange periodic funding payments (see core/risk/funding.py) that pull
    its price back toward the underlying spot index.

    market_value/unrealized_pnl are identical to Future's - the multiplier
    scaling is the same mechanic. What's different is funding, which is
    computed separately since it isn't part of mark-to-market PnL.
    """

    def __init__(self, symbol, multiplier=1):
        super().__init__(symbol)
        self.multiplier = multiplier

    def market_value(self, quantity, current_price):
        return quantity * current_price * self.multiplier

    def unrealized_pnl(self, quantity, entry_price, current_price):
        return quantity * (current_price - entry_price) * self.multiplier
