import numpy as np
import yfinance as yf


Z_SCORES = {0.95: 1.645, 0.99: 2.33}


def compute_portfolio_var(portfolio, prices, confidence=0.95, lookback_days=90):
    """
    Parametric (variance-covariance) 1-day VaR.

    1. Pull historical daily prices for every symbol in the portfolio
    2. Compute daily returns and their covariance matrix
    3. Combine with each position's current dollar exposure
    4. VaR = z-score * portfolio standard deviation
    """
    symbols = list(portfolio.positions.keys())

    exposures = np.array([
        portfolio.positions[s].market_value(prices[s]) for s in symbols
    ])

    hist = yf.download(symbols, period=f"{lookback_days}d", progress=False, threads=False)["Close"]
    if len(symbols) == 1:
        hist = hist.to_frame(name=symbols[0])

    returns = hist.pct_change()
    cov_matrix = returns.cov().reindex(index=symbols, columns=symbols).values

    portfolio_variance = exposures @ cov_matrix @ exposures
    portfolio_std_dev = np.sqrt(portfolio_variance)

    z = Z_SCORES.get(confidence, 1.645)
    return z * portfolio_std_dev