from core.products.perpetual import Perpetual

# Binance, OKX, and Bybit all settle perp funding every 8 hours.
FUNDING_INTERVALS_PER_DAY = 3


def funding_pnl(position, funding_rate, current_price):
    """
    PnL from a single funding settlement, in quote-currency terms.

    Funding transfers cash directly between longs and shorts to keep a
    perpetual's price anchored to the spot index - there's no counterparty
    exchange and no convergence at expiry the way there is for a dated
    Future. When funding_rate > 0 (perp trading above spot, longs crowded
    in) longs pay shorts; when funding_rate < 0, shorts pay longs.
    """
    notional = position.market_value(current_price)
    return -notional * funding_rate


def portfolio_funding_pnl(portfolio, funding_rates, prices):
    """
    Total funding PnL across every Perpetual position in the portfolio for
    one funding settlement. Non-perpetual positions are ignored - funding
    only applies to perps.
    """
    total = 0.0
    for symbol, position in portfolio.positions.items():
        if not isinstance(position.instrument, Perpetual):
            continue
        total += funding_pnl(position, funding_rates[symbol], prices[symbol])
    return total


def annualized_funding_yield(funding_rate, intervals_per_day=FUNDING_INTERVALS_PER_DAY):
    """
    A single funding settlement's rate, expressed as an annualized carry -
    the number market makers actually compare against cost of capital when
    sizing a cash-and-carry (long spot / short perp, or the reverse) trade.
    Crypto trades 24/7, so this compounds by calendar days, not trading days.
    """
    return funding_rate * intervals_per_day * 365
