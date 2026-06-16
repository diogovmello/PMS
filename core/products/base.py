from abc import ABC, abstractmethod


class Instrument(ABC):
    """
    Abstract base for all tradeable products (equities, futures, options...).
    Each subclass implements its own valuation and PnL logic.
    """

    def __init__(self, symbol):
        self.symbol = symbol

    @abstractmethod
    def market_value(self, quantity, current_price):
        raise NotImplementedError

    @abstractmethod
    def unrealized_pnl(self, quantity, entry_price, current_price):
        raise NotImplementedError