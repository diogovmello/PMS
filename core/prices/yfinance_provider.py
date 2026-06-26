import yfinance as yf
from core.prices.base import PriceProvider


class YFinancePriceProvider(PriceProvider):
    """Fetches current prices from Yahoo Finance via the yfinance library."""

    def get_prices(self, symbols):
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