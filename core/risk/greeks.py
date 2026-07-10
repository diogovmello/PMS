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


def _validate_time_to_expiry(time_to_expiry):
    if time_to_expiry <= 0:
        raise ValueError(
            f"time_to_expiry must be positive, got {time_to_expiry} - option has already expired"
        )


def _n_pdf(x):
    """Standard normal PDF."""
    return math.exp(-0.5 * x ** 2) / math.sqrt(2 * math.pi)


def _n_cdf(x):
    """Standard normal CDF, via the error function - avoids adding scipy as a dependency."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _d1_d2(underlying_price, strike, time_to_expiry, volatility, risk_free_rate):
    d1 = (
        math.log(underlying_price / strike)
        + (risk_free_rate + 0.5 * volatility ** 2) * time_to_expiry
    ) / (volatility * math.sqrt(time_to_expiry))
    d2 = d1 - volatility * math.sqrt(time_to_expiry)
    return d1, d2


def black_scholes_delta(underlying_price, strike, time_to_expiry, volatility,
                         option_type, risk_free_rate=0.04):
    """
    Black-Scholes delta: sensitivity of the option's price to a $1 move
    in the underlying. Calls: between 0 and 1. Puts: between -1 and 0.
    """
    _validate_time_to_expiry(time_to_expiry)
    d1, _ = _d1_d2(underlying_price, strike, time_to_expiry, volatility, risk_free_rate)
    n_d1 = _n_cdf(d1)

    if option_type == "call":
        return n_d1
    elif option_type == "put":
        return n_d1 - 1
    else:
        raise ValueError(f"Unknown option_type: {option_type}")


def black_scholes_gamma(underlying_price, strike, time_to_expiry, volatility, risk_free_rate=0.04):
    """
    Black-Scholes gamma: sensitivity of delta to a $1 move in the underlying.
    Same value for calls and puts.
    """
    _validate_time_to_expiry(time_to_expiry)
    d1, _ = _d1_d2(underlying_price, strike, time_to_expiry, volatility, risk_free_rate)
    return _n_pdf(d1) / (underlying_price * volatility * math.sqrt(time_to_expiry))


def black_scholes_vega(underlying_price, strike, time_to_expiry, volatility, risk_free_rate=0.04):
    """
    Black-Scholes vega: sensitivity of the option's price to a 1.0 (100
    percentage point) move in volatility. Same value for calls and puts.
    Divide by 100 for the more commonly quoted "price change per 1 vol point".
    """
    _validate_time_to_expiry(time_to_expiry)
    d1, _ = _d1_d2(underlying_price, strike, time_to_expiry, volatility, risk_free_rate)
    return underlying_price * _n_pdf(d1) * math.sqrt(time_to_expiry)


def black_scholes_theta(underlying_price, strike, time_to_expiry, volatility,
                         option_type, risk_free_rate=0.04):
    """
    Black-Scholes theta: rate of option value decay per calendar day, all else
    held fixed. Negative for a long option position (value erodes as expiry
    approaches).
    """
    _validate_time_to_expiry(time_to_expiry)
    d1, d2 = _d1_d2(underlying_price, strike, time_to_expiry, volatility, risk_free_rate)
    decay_term = -(underlying_price * _n_pdf(d1) * volatility) / (2 * math.sqrt(time_to_expiry))
    discounted_strike = risk_free_rate * strike * math.exp(-risk_free_rate * time_to_expiry)

    if option_type == "call":
        annual_theta = decay_term - discounted_strike * _n_cdf(d2)
    elif option_type == "put":
        annual_theta = decay_term + discounted_strike * _n_cdf(-d2)
    else:
        raise ValueError(f"Unknown option_type: {option_type}")

    return annual_theta / 365


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


def compute_option_greeks(option, underlying_price, lookback_days=90, risk_free_rate=0.04):
    """
    Full Greeks (delta, gamma, theta, vega) for a single Option instrument,
    using its own underlying/strike/expiry. Fetches volatility/time-to-expiry
    once and reuses them across all four, rather than recomputing per-Greek.
    """
    volatility = historical_volatility(option.underlying, lookback_days)
    t = time_to_expiry_years(option.expiry)
    common = dict(
        underlying_price=underlying_price,
        strike=option.strike,
        time_to_expiry=t,
        volatility=volatility,
        risk_free_rate=risk_free_rate,
    )
    return {
        "delta": black_scholes_delta(option_type=option.option_type, **common),
        "gamma": black_scholes_gamma(**common),
        "theta": black_scholes_theta(option_type=option.option_type, **common),
        "vega": black_scholes_vega(**common),
    }
