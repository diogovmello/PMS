from core.products.equity import Equity


class Position:
    def __init__(self, symbol, quantity, entry_price, instrument=None):
        self.symbol = symbol
        self.quantity = quantity
        self.entry_price = entry_price
        self.instrument = instrument or Equity(symbol)

    def market_value(self, current_price):
        return self.instrument.market_value(self.quantity, current_price)

    def unrealized_pnl(self, current_price):
        return self.instrument.unrealized_pnl(self.quantity, self.entry_price, current_price)

    def __repr__(self):
        return f"Position({self.symbol}, qty={self.quantity}, entry={self.entry_price})"


class Portfolio:
    def __init__(self):
        self.positions = {}

    def add_position(self, symbol, quantity, entry_price, instrument=None):
        self.positions[symbol] = Position(symbol, quantity, entry_price, instrument)

    def get_position(self, symbol):
        return self.positions.get(symbol)

    def total_market_value(self, prices):
        return sum(p.market_value(prices[s]) for s, p in self.positions.items())

    def total_unrealized_pnl(self, prices):
        return sum(p.unrealized_pnl(prices[s]) for s, p in self.positions.items())