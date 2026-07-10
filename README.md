# PMS — Portfolio Management System

A Python-based portfolio management system built from scratch to model how a real buy-side risk and position-tracking stack works: position ingestion, instrument-aware P&L, live market data, and portfolio risk (exposure and parametric VaR), with multi-portfolio-manager support out of the box. Covers both traditional instruments (equities, futures, options) and crypto perpetual futures with funding-rate carry.

This project is a learning exercise in systems design as much as it is in finance — every module is built behind an interface so the underlying implementation (CSV vs. a live broker feed, a free market data API vs. a paid vendor) can be swapped without touching the engine that depends on it.

## Architecture

```
PMS/
├── core/
│   ├── products/            # Instrument hierarchy - one class per product type
│   │   ├── base.py          # Abstract Instrument (market_value, unrealized_pnl)
│   │   ├── equity.py        # Vanilla equities/ETFs
│   │   ├── future.py        # Futures - PnL scaled by contract multiplier
│   │   ├── option.py        # Options - live-priced, OCC contract symbols
│   │   ├── perpetual.py     # Perpetual futures (crypto) - no expiry, funded instead
│   │   └── factory.py       # Builds the right Instrument from a product_type string
│   ├── loaders/               # Position ingestion
│   │   ├── base.py           # Abstract PositionLoader
│   │   ├── csv_loader.py     # EOD CSV loader, splits multi-PM files by `pm` column
│   │   └── order_based_loader.py  # Replays FILLED orders into positions (average-cost accounting)
│   ├── orders/                # Order book - the source of truth behind order_based_loader
│   │   ├── order.py          # Order dataclass
│   │   ├── db.py             # SQLite schema (orders, processed_files)
│   │   ├── repository.py     # Insert/query orders
│   │   └── ingestion.py      # Replays incoming order CSVs into the DB, once each
│   ├── prices/                # Market data
│   │   ├── base.py           # Abstract PriceProvider
│   │   ├── yfinance_provider.py  # Live prices via Yahoo Finance; options via the live option chain
│   │   └── binance_perp_provider.py  # Live mark price + funding rate via Binance's public futures API
│   ├── risk/                  # Portfolio risk
│   │   ├── exposure.py       # Gross / net / per-symbol dollar exposure
│   │   ├── var.py            # Parametric (variance-covariance) 1-day VaR
│   │   ├── greeks.py         # Black-Scholes delta
│   │   └── funding.py        # Perpetual funding PnL and annualized funding yield
│   └── position.py            # Position and Portfolio - the engine's core data model
├── api/                       # Web layer (planned - see Roadmap)
├── data/
│   └── sample_positions.csv  # Sample multi-PM EOD file (equity, future, option)
├── tests/                     # pytest suite - no network or real DB access required
├── requirements.txt
└── requirements-dev.txt       # requirements.txt + pytest
```

## Design decisions

**Instrument hierarchy over conditional branching.** Every product type (`Equity`, `Future`, `Option`) implements the same two-method `Instrument` interface — `market_value()` and `unrealized_pnl()` — instead of routing through a single function with `if product_type == ...` branches. `Position` holds an `Instrument` and delegates to it. Adding a new product type later (bonds, FX) means writing one new class, not touching existing code.

**Position and price sourcing are both behind interfaces.** `PositionLoader` and `PriceProvider` are abstract base classes with one concrete implementation each today (`CSVPositionLoader`, `YFinancePriceProvider`). Neither the risk engine nor the P&L logic knows or cares where the data came from. This is deliberate: a live broker feed (e.g. IBKR) or a paid market data vendor can replace either implementation without any change to `core/position.py` or `core/risk/`.

**Multi-PM data model.** Real EOD position files from a prime broker or custodian typically contain every portfolio manager's book in one file, disambiguated by an account/strategy column. `CSVPositionLoader` mirrors this: it reads a single CSV with a `pm` column and returns `{pm_name: Portfolio}`, so the rest of the system operates on one portfolio at a time regardless of how many PMs are in the file.

**Parametric VaR, not historical or Monte Carlo.** `compute_portfolio_var()` uses the variance-covariance method: pull trailing daily returns per symbol from Yahoo Finance, build a covariance matrix, and scale by each position's current dollar exposure:

```
VaR = z * sqrt(wᵗ Σ w)
```

where `w` is the vector of dollar exposures (not weights) and `Σ` is the return covariance matrix. This assumes returns are normally distributed, which is the standard simplification for a first-pass risk number — historical simulation and Monte Carlo are listed in the Roadmap as more realistic (and more expensive) alternatives. Known limitation: newly listed instruments (e.g. a stock that just IPO'd) have a shorter price history than the lookback window, which can leave gaps in the covariance matrix — `pandas.DataFrame.cov()` handles this via pairwise-NaN exclusion, but it's a real edge case in the current implementation, not a hidden one.

**Options are priced and risked off the underlying, not the contract itself.** Yahoo Finance doesn't serve historical daily bars or `yf.download`-style quotes for an individual OCC option contract, only a live option-chain snapshot. So `YFinancePriceProvider` parses the OCC symbol (e.g. `AAPL260717C00300000`) to get the underlying/expiry/type and pulls the live quote from `Ticker(underlying).option_chain(expiry)`, while `compute_portfolio_var()` uses the underlying's historical returns as a proxy for the option's own (unavailable) return series. That proxy isn't delta-scaled, so it's a simplification, not a full options VaR model — a truer treatment would weight the underlying's return series by the position's Black-Scholes delta (see `core/risk/greeks.py`) rather than using it directly.

**Perpetuals are funded, not marked-to-market alone.** A `Perpetual`'s `market_value()`/`unrealized_pnl()` are identical to `Future`'s - same multiplier-scaled mechanic. What's genuinely different is that a perp never expires and never converges to spot at a settlement date; instead it trades at a persistent premium or discount to the spot index, and periodic funding payments between longs and shorts (`core/risk/funding.py`) are what pull it back into line. That's modeled as a separate PnL stream (`funding_pnl`, `portfolio_funding_pnl`) rather than folded into `unrealized_pnl`, since it settles on its own schedule (every 8 hours on Binance/OKX/Bybit) independent of mark-to-market. `annualized_funding_yield` expresses a single settlement's rate as a carry number, compounding by calendar day (not trading day) since crypto trades 24/7 - the number a cash-and-carry trade (long spot, short perp, or the reverse) is actually sized against.

**CSV and yfinance over live broker/vendor integration, for now.** A live IBKR feed or a paid data vendor would add authentication, async handling, and market-data-subscription complexity that has nothing to do with portfolio management logic itself. Starting with file-based ingestion and a free market data API kept the focus on the engine; the abstraction layers above mean swapping either one in later is a contained change.

## Quickstart

```bash
git clone https://github.com/diogovmello/PMS.git
cd PMS
python -m venv venv
source venv/Scripts/activate   # Windows (Git Bash); use venv/bin/activate on macOS/Linux
pip install -r requirements.txt
```

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

The suite (`tests/`) runs in under a couple of seconds because market-data calls (`yf.download`, `Ticker.option_chain`) and the orders SQLite DB are stubbed/pointed at a temp file per test (see `tests/conftest.py`) - no network access or `data/orders.db` writes required to run it.

## Example usage

```python
from core.loaders.csv_loader import CSVPositionLoader
from core.prices.yfinance_provider import YFinancePriceProvider
from core.risk.exposure import gross_exposure, net_exposure
from core.risk.var import compute_portfolio_var

portfolios = CSVPositionLoader("data/sample_positions.csv").load()

symbols = {s for portfolio in portfolios.values() for s in portfolio.positions}
prices = YFinancePriceProvider().get_prices(list(symbols))

for pm, portfolio in portfolios.items():
    print(f"{pm} unrealized PnL:", portfolio.total_unrealized_pnl(prices))
    print(f"{pm} gross exposure:", gross_exposure(portfolio, prices))
    print(f"{pm} 1-day VaR (95%):", compute_portfolio_var(portfolio, prices))
```

## Input file format

`data/sample_positions.csv` is the reference format for the CSV loader:

| Column | Required | Notes |
|---|---|---|
| `pm` | Yes | Portfolio manager / account identifier |
| `symbol` | Yes | Ticker (equities/futures) or OCC-style contract code (options) |
| `quantity` | Yes | Signed - negative for short positions |
| `entry_price` | Yes | Cost basis |
| `product_type` | No (defaults to `equity`) | `equity`, `future`, `option`, or `perpetual` |
| `multiplier` | No | Contract size - defaults to 1 (equity/perpetual), required for futures, defaults to 100 for options |
| `strike`, `expiry`, `option_type` | Only for options | Used by the `Option` instrument; `option_type` is `call` or `put` |

## Current features

- Instrument hierarchy: equities, futures (contract multiplier), options (live-priced), crypto perpetuals (funded, not expiry-dated)
- Multi-PM position loading from a single EOD CSV, or replayed from a SQLite order book (average-cost accounting)
- Live pricing via Yahoo Finance (`yfinance`) for equities/futures/options, and Binance's public futures API for perp mark price + funding rate
- Portfolio risk: gross/net/per-symbol exposure, parametric VaR, Black-Scholes delta, perpetual funding PnL and annualized funding yield

## Crypto perpetuals example

```python
from core.position import Portfolio
from core.products.perpetual import Perpetual
from core.prices.binance_perp_provider import BinancePerpPriceProvider
from core.risk.funding import portfolio_funding_pnl, annualized_funding_yield

provider = BinancePerpPriceProvider()
portfolio = Portfolio()
portfolio.add_position("BTCUSDT", quantity=0.5, entry_price=63000, instrument=Perpetual("BTCUSDT"))
portfolio.add_position("ETHUSDT", quantity=-4, entry_price=3500, instrument=Perpetual("ETHUSDT"))

symbols = list(portfolio.positions)
prices = provider.get_prices(symbols)
funding_rates = provider.get_funding_rates(symbols)

print("unrealized PnL:", portfolio.total_unrealized_pnl(prices))
print("funding PnL this settlement:", portfolio_funding_pnl(portfolio, funding_rates, prices))
for symbol, rate in funding_rates.items():
    print(f"{symbol} annualized funding yield: {annualized_funding_yield(rate):.2%}")
```

## Roadmap

- [x] Black-Scholes delta for options
- [x] Automated test suite (pytest)
- [ ] Full Greeks (gamma, theta, vega) for options
- [x] Crypto perpetual futures with funding-rate carry PnL
- [ ] Spot-perp basis metric (the signal behind cash-and-carry/funding-arb trades)
- [ ] 24/7 (365-day) annualization for `compute_portfolio_var` when a portfolio holds crypto positions - it currently always uses the 252-trading-day equity convention
- [ ] Web UI (FastAPI/Flask backend + frontend) for positions, P&L, and risk
- [ ] CI via GitHub Actions
- [ ] Historical-simulation and/or Monte Carlo VaR as alternatives to parametric
- [ ] Live position feed (e.g. IBKR) as a second `PositionLoader` implementation
- [ ] License

## Tech stack

Python 3, [yfinance](https://github.com/ranaroussi/yfinance), NumPy, pandas (via yfinance), [requests](https://requests.readthedocs.io/) (Binance public API)