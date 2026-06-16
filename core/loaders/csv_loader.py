import csv
from core.loaders.base import PositionLoader
from core.position import Portfolio


class CSVPositionLoader(PositionLoader):
    """
    Loads positions from an EOD CSV file.
    Expected columns: pm, symbol, quantity, entry_price

    Positions are grouped by PM - each PM gets their own Portfolio.
    """

    def __init__(self, filepath):
        self.filepath = filepath

    def load(self):
        portfolios = {}
        with open(self.filepath, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pm = row["pm"]
                if pm not in portfolios:
                    portfolios[pm] = Portfolio()
                portfolios[pm].add_position(
                    symbol=row["symbol"],
                    quantity=float(row["quantity"]),
                    entry_price=float(row["entry_price"]),
                )
        return portfolios