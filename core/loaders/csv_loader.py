import csv
from core.loaders.base import PositionLoader
from core.position import Portfolio
from core.products.factory import build_instrument


class CSVPositionLoader(PositionLoader):
    """
    Loads positions from an EOD CSV file.
    Required columns: pm, symbol, quantity, entry_price
    Optional columns: product_type (default 'equity'), multiplier (default 1)

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

                instrument = build_instrument(
                    symbol=row["symbol"],
                    product_type=row.get("product_type", "equity"),
                    multiplier=row.get("multiplier"),
                    strike=row.get("strike"),
                    expiry=row.get("expiry"),
                    option_type=row.get("option_type"),
                )

                portfolios[pm].add_position(
                    symbol=row["symbol"],
                    quantity=float(row["quantity"]),
                    entry_price=float(row["entry_price"]),
                    instrument=instrument,
                )
        return portfolios