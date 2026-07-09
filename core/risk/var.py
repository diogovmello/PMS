import numpy as np
import yfinance as yf

from core.products.option import Option


Z_SCORES = {0.95: 1.645, 0.99: 2.33}


def _return_series_symbol(position):
    """
    Symbol to pull historical daily prices for, for this position's return
    series. Option contracts don't have a reliable historical daily series
    on Yahoo Finance (unlike a live option-chain quote), so options use
    their underlying's returns as a proxy instead of their own.
    """
    if isinstance(position.instrument, Option):
        return position.instrument.underlying
    return position.symbol


def compute_portfolio_var(portfolio, prices, confidence=0.95, lookback_days=90):
    """
    Parametric (variance-covariance) 1-day VaR.

    1. Pull historical daily prices for every symbol in the portfolio
       (options use their underlying's price history as a proxy - see
       `_return_series_symbol`)
    2. Compute daily returns and their covariance matrix
    3. Combine with each position's current dollar exposure
    4. VaR = z-score * portfolio standard deviation
    """
    if confidence not in Z_SCORES:
        raise ValueError(f"Unsupported confidence level: {confidence}. Supported: {sorted(Z_SCORES)}")

    symbols = list(portfolio.positions.keys())
    return_symbols = [_return_series_symbol(portfolio.positions[s]) for s in symbols]

    exposures = np.array([
        portfolio.positions[s].market_value(prices[s]) for s in symbols
    ])

    fetch_symbols = sorted(set(return_symbols))
    hist = yf.download(fetch_symbols, period=f"{lookback_days}d", progress=False, threads=False)["Close"]
    if len(fetch_symbols) == 1:
        hist = hist.to_frame(name=fetch_symbols[0])

    returns = hist.pct_change()
    cov_matrix = returns.cov().reindex(index=return_symbols, columns=return_symbols).values

    portfolio_variance = exposures @ cov_matrix @ exposures
    portfolio_std_dev = np.sqrt(portfolio_variance)

    z = Z_SCORES[confidence]
    return z * portfolio_std_dev