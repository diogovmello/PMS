import yfinance as yf
from core.prices.base import PriceProvider


class YFinancePriceProvider(PriceProvider):
    """Fetches current prices from Yahoo Finance via the yfinance library."""

    def get_prices(self, symbols):
        data = yf.download(symbols, period="1d", progress=False, threads=False)
        closes = data["Close"]

        prices = {}
        for symbol in symbols:
            # yf.download shapes the result differently for one symbol
            # (a Series) vs multiple symbols (a DataFrame with one column each).
            if len(symbols) == 1:
                prices[symbol] = closes.iloc[-1]
            else:
                prices[symbol] = closes[symbol].iloc[-1]
        return prices