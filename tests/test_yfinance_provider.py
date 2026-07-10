from core.prices.yfinance_provider import _parse_occ_symbol


class TestParseOccSymbol:
    def test_parses_call_contract(self):
        assert _parse_occ_symbol("AAPL260717C00300000") == ("AAPL", "2026-07-17", "call")

    def test_parses_put_contract(self):
        assert _parse_occ_symbol("AAPL260717P00300000") == ("AAPL", "2026-07-17", "put")

    def test_parses_strike_with_decimals(self):
        # 00007500 -> $7.50 strike, only the type/underlying/expiry are returned
        underlying, expiry, option_type = _parse_occ_symbol("TSLA271231C00007500")
        assert underlying == "TSLA"
        assert expiry == "2027-12-31"
        assert option_type == "call"

    def test_plain_equity_ticker_is_not_occ(self):
        assert _parse_occ_symbol("AAPL") is None

    def test_future_ticker_is_not_occ(self):
        assert _parse_occ_symbol("ES=F") is None

    def test_ticker_with_dot_is_not_occ(self):
        assert _parse_occ_symbol("BRK.B") is None
