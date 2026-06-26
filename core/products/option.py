from core.products.base import Instrument


class Option(Instrument):
    """
    Vanilla option contract (call or put). PnL uses the live quoted
    option price, scaled by a multiplier (100 shares per contract).

    `underlying` is the stock ticker the option is written on (e.g. AAPL),
    used by the Greeks calculation - separate from `symbol`, which is the
    option's own OCC contract code.
    """

    def __init__(self, symbol, strike, expiry, option_type, underlying, multiplier=100):
        super().__init__(symbol)
        self.strike = strike
        self.expiry = expiry
        self.option_type = option_type.lower()
        self.underlying = underlying
        self.multiplier = multiplier

    def market_value(self, quantity, current_price):
        return quantity * current_price * self.multiplier

    def unrealized_pnl(self, quantity, entry_price, current_price):
        return quantity * (current_price - entry_price) * self.multiplier