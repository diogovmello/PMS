import math
from datetime import date

import yfinance as yf


def historical_volatility(symbol, lookback_days=90):
    """Annualized volatility of daily returns over the lookback window."""
    hist = yf.download(symbol, period=f"{lookback_days}d", progress=False, threads=False)["Close"]
    if hasattr(hist, "columns"):
        hist = hist[symbol]  # select the single symbol's column explicitly
    returns = hist.pct_change().dropna()
    daily_vol = returns.std()
    return daily_vol * math.sqrt(252)


def time_to_expiry_years(expiry, as_of=None):
    as_of = as_of or date.today()
    expiry_date = date.fromisoformat(expiry)
    return (expiry_date - as_of).days / 365


def black_scholes_delta(underlying_price, strike, time_to_expiry, volatility,
                         option_type, risk_free_rate=0.04):
    """
    Black-Scholes delta: sensitivity of the option's price to a $1 move
    in the underlying. Calls: between 0 and 1. Puts: between -1 and 0.
    """
    if time_to_expiry <= 0:
        raise ValueError(
            f"time_to_expiry must be positive, got {time_to_expiry} - option has already expired"
        )

    d1 = (
        math.log(underlying_price / strike)
        + (risk_free_rate + 0.5 * volatility ** 2) * time_to_expiry
    ) / (volatility * math.sqrt(time_to_expiry))

    # Normal CDF via the error function - avoids adding scipy as a dependency
    n_d1 = 0.5 * (1 + math.erf(d1 / math.sqrt(2)))

    if option_type == "call":
        return n_d1
    elif option_type == "put":
        return n_d1 - 1
    else:
        raise ValueError(f"Unknown option_type: {option_type}")


def compute_option_delta(option, underlying_price, lookback_days=90, risk_free_rate=0.04):
    """Delta for a single Option instrument, using its own underlying/strike/expiry."""
    volatility = historical_volatility(option.underlying, lookback_days)
    t = time_to_expiry_years(option.expiry)
    return black_scholes_delta(
        underlying_price=underlying_price,
        strike=option.strike,
        time_to_expiry=t,
        volatility=volatility,
        option_type=option.option_type,
        risk_free_rate=risk_free_rate,
    )