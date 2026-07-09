import re
from datetime import datetime

import yfinance as yf
from core.prices.base import PriceProvider

_OCC_SYMBOL_RE = re.compile(r"^([A-Z.]+)(\d{6})([CP])(\d{8})$")


def _parse_occ_symbol(symbol):
    """
    Parse an OCC-style option contract symbol (e.g. AAPL260717C00300000)
    into (underlying, expiry 'YYYY-MM-DD', option_type). Returns None if
    `symbol` isn't OCC-formatted, i.e. it's an equity/future ticker.
    """
    match = _OCC_SYMBOL_RE.match(symbol)
    if not match:
        return None
    underlying, date_str, cp, _strike_str = match.groups()
    expiry = datetime.strptime(date_str, "%y%m%d").strftime("%Y-%m-%d")
    return underlying, expiry, "call" if cp == "C" else "put"


class YFinancePriceProvider(PriceProvider):
    """
    Fetches current prices from Yahoo Finance via the yfinance library.

    Equity/future tickers are priced off the latest daily close. Options
    can't be priced that way - `yf.download` only serves OHLC history for
    plain tickers, not option contract quotes - so OCC-formatted symbols
    are routed to the underlying's live option chain instead.
    """

    def get_prices(self, symbols):
        equity_like = [s for s in symbols if _parse_occ_symbol(s) is None]
        option_like = [s for s in symbols if _parse_occ_symbol(s) is not None]

        prices = {}
        if equity_like:
            prices.update(self._get_equity_prices(equity_like))
        for symbol in option_like:
            prices[symbol] = self._get_option_price(symbol)
        return prices

    def _get_equity_prices(self, symbols):
        data = yf.download(symbols, period="1d", progress=False, threads=False)
        closes = data["Close"]

        prices = {}
        for symbol in symbols:
            if hasattr(closes, "columns"):
                # DataFrame - one column per symbol, regardless of how many symbols
                prices[symbol] = closes[symbol].iloc[-1]
            else:
                # Bare Series - only happens in some yfinance versions/edge cases
                prices[symbol] = closes.iloc[-1]
        return prices

    def _get_option_price(self, symbol):
        underlying, expiry, option_type = _parse_occ_symbol(symbol)
        chain = yf.Ticker(underlying).option_chain(expiry)
        table = chain.calls if option_type == "call" else chain.puts
        row = table[table["contractSymbol"] == symbol]
        if row.empty:
            raise ValueError(f"No quote found for option contract: {symbol}")
        return float(row["lastPrice"].iloc[0])
