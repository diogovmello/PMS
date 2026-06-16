from abc import ABC, abstractmethod


class PositionLoader(ABC):
    """
    Abstract base for anything that loads positions, grouped by PM.
    A CSV loader, a database loader, or a future live IBKR feed all
    implement this same interface - the rest of the PMS never needs
    to know which one is in use.
    """

    @abstractmethod
    def load(self):
        """Load positions and return a dict of {pm_name: Portfolio}."""
        raise NotImplementedError