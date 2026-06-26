from core.products.base import Instrument


class Option(Instrument):
    """
    Vanilla option contract (call or put). PnL uses the live quoted
    option price, scaled by a multiplier (100 shares per contract,
    the US equity-options standard).

    strike, expiry, and option_type aren't used in the PnL math yet -
    they identify the contract, and will feed Black-Scholes/Greeks
    later in the risk metrics phase.
    """

    def __init__(self, symbol, strike, expiry, option_type, multiplier=100):
        super().__init__(symbol)
        self.strike = strike
        self.expiry = expiry
        self.option_type = option_type.lower()  # 'call' or 'put'
        self.multiplier = multiplier

    def market_value(self, quantity, current_price):
        return quantity * current_price * self.multiplier

    def unrealized_pnl(self, quantity, entry_price, current_price):
        return quantity * (current_price - entry_price) * self.multiplier