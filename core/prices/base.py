from abc import ABC, abstractmethod


class PriceProvider(ABC):
    """
    Abstract base for anything that supplies current prices.
    A live API, a CSV file, or a different vendor feed could all
    implement this same interface - the rest of the PMS doesn't
    need to know which one is in use.
    """

    @abstractmethod
    def get_prices(self, symbols):
        """Return a dict of {symbol: current_price} for the given symbols."""
        raise NotImplementedError