from core.products.equity import Equity
from core.products.future import Future


def build_instrument(symbol, product_type="equity", multiplier=1):
    product_type = (product_type or "equity").lower()

    if product_type == "equity":
        return Equity(symbol)
    elif product_type == "future":
        return Future(symbol, multiplier=float(multiplier or 1))
    else:
        raise ValueError(f"Unknown product_type: {product_type}")