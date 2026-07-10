import requests

from core.prices.base import PriceProvider

BINANCE_FUTURES_BASE_URL = "https://fapi.binance.com"


class BinancePerpPriceProvider(PriceProvider):
    """
    Fetches perpetual futures mark price and funding rate from Binance's
    public USDT-margined futures API - no API key required for these
    endpoints. Symbols are Binance's own perp tickers (e.g. "BTCUSDT"), not
    equity-style tickers.

    Mark price, not last-traded price, is used deliberately: it's the price
    exchanges actually use for margining/liquidation and is manipulation-
    resistant (blended from the index and a funding-basis estimate), so it's
    the more honest number for portfolio valuation.
    """

    def __init__(self, base_url=BINANCE_FUTURES_BASE_URL, timeout=10):
        self.base_url = base_url
        self.timeout = timeout

    def get_prices(self, symbols):
        return {symbol: data["markPrice"] for symbol, data in self._fetch(symbols).items()}

    def get_funding_rates(self, symbols):
        """Current funding rate per symbol - specific to perps, not part of the PriceProvider interface."""
        return {symbol: data["fundingRate"] for symbol, data in self._fetch(symbols).items()}

    def _fetch(self, symbols):
        response = requests.get(f"{self.base_url}/fapi/v1/premiumIndex", timeout=self.timeout)
        response.raise_for_status()
        by_symbol = {row["symbol"]: row for row in response.json()}

        missing = [s for s in symbols if s not in by_symbol]
        if missing:
            raise ValueError(f"No Binance perpetual data for symbols: {missing}")

        return {
            symbol: {
                "markPrice": float(by_symbol[symbol]["markPrice"]),
                "fundingRate": float(by_symbol[symbol]["lastFundingRate"]),
            }
            for symbol in symbols
        }
