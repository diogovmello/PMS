from core.products.equity import Equity
from core.products.future import Future
from core.products.option import Option


def build_instrument(symbol, product_type="equity", multiplier=None,
                      strike=None, expiry=None, option_type=None):
    product_type = (product_type or "equity").lower()

    if product_type == "equity":
        return Equity(symbol)
    elif product_type == "future":
        return Future(symbol, multiplier=float(multiplier or 1))
    elif product_type == "option":
        return Option(
            symbol,
            strike=float(strike),
            expiry=expiry,
            option_type=option_type,
            multiplier=float(multiplier or 100),
        )
    else:
        raise ValueError(f"Unknown product_type: {product_type}")