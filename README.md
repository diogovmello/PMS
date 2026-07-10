# PMS — Portfolio Management System

A Python-based portfolio management system built from scratch to model how a real buy-side risk and position-tracking stack works: position ingestion, instrument-aware P&L, live market data, and portfolio risk (exposure and parametric VaR), with multi-portfolio-manager support out of the box.

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
│   │   └── yfinance_provider.py  # Live prices via Yahoo Finance; options via the live option chain
│   ├── risk/                  # Portfolio risk
│   │   ├── exposure.py       # Gross / net / per-symbol dollar exposure
│   │   ├── var.py            # Parametric (variance-covariance) 1-day VaR
│   │   └── greeks.py         # Black-Scholes delta
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
| `product_type` | No (defaults to `equity`) | `equity`, `future`, or `option` |
| `multiplier` | No | Contract size - defaults to 1 (equity), required for futures, defaults to 100 for options |
| `strike`, `expiry`, `option_type` | Only for options | Used by the `Option` instrument; `option_type` is `call` or `put` |

## Current features

- Instrument hierarchy: equities, futures (contract multiplier), options (live-priced)
- Multi-PM position loading from a single EOD CSV, or replayed from a SQLite order book (average-cost accounting)
- Live pricing via Yahoo Finance (`yfinance`), including live option-chain quotes for OCC contracts
- Portfolio risk: gross/net/per-symbol exposure, parametric VaR, Black-Scholes delta

## Roadmap

- [x] Black-Scholes delta for options
- [x] Automated test suite (pytest)
- [ ] Full Greeks (gamma, theta, vega) for options
- [ ] Web UI (FastAPI/Flask backend + frontend) for positions, P&L, and risk
- [ ] CI via GitHub Actions
- [ ] Historical-simulation and/or Monte Carlo VaR as alternatives to parametric
- [ ] Live position feed (e.g. IBKR) as a second `PositionLoader` implementation
- [ ] License

## Tech stack

Python 3, [yfinance](https://github.com/ranaroussi/yfinance), NumPy, pandas (via yfinance)