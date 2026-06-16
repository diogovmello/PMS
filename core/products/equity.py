from core.products.base import Instrument


class Equity(Instrument):
    """Vanilla equity: stocks, ETFs. No multiplier, no expiry."""

    def market_value(self, quantity, current_price):
        return quantity * current_price

    def unrealized_pnl(self, quantity, entry_price, current_price):
        return quantity * (current_price - entry_price)