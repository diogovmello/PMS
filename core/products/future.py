from core.products.base import Instrument


class Future(Instrument):
    """
    Vanilla futures contract. PnL scales by a multiplier (contract size),
    e.g. the E-mini S&P 500 (ES) has a multiplier of 50.
    """

    def __init__(self, symbol, multiplier):
        super().__init__(symbol)
        self.multiplier = multiplier

    def market_value(self, quantity, current_price):
        return quantity * current_price * self.multiplier

    def unrealized_pnl(self, quantity, entry_price, current_price):
        return quantity * (current_price - entry_price) * self.multiplier