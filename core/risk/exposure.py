def gross_exposure(portfolio, prices):
    """Sum of absolute dollar exposure across all positions - total size at risk, ignoring direction."""
    return sum(abs(p.market_value(prices[s])) for s, p in portfolio.positions.items())


def net_exposure(portfolio, prices):
    """Sum of signed dollar exposure - what's left after longs and shorts offset."""
    return sum(p.market_value(prices[s]) for s, p in portfolio.positions.items())


def exposure_by_symbol(portfolio, prices):
    """Dollar exposure broken out per symbol."""
    return {s: p.market_value(prices[s]) for s, p in portfolio.positions.items()}