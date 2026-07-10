import pytest

from core.loaders.csv_loader import CSVPositionLoader
from core.products.equity import Equity
from core.products.future import Future
from core.products.option import Option


def _write_csv(path, rows, header):
    lines = [",".join(header)]
    lines += [",".join(str(v) for v in row) for row in rows]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def test_splits_positions_by_pm(tmp_path):
    header = ["pm", "symbol", "quantity", "entry_price"]
    rows = [
        ["smith", "AAPL", 100, 150],
        ["jones", "TSLA", 20, 700],
    ]
    csv_path = _write_csv(tmp_path / "positions.csv", rows, header)

    portfolios = CSVPositionLoader(str(csv_path)).load()

    assert set(portfolios.keys()) == {"smith", "jones"}
    assert "AAPL" in portfolios["smith"].positions
    assert "TSLA" in portfolios["jones"].positions


def test_product_type_defaults_to_equity(tmp_path):
    header = ["pm", "symbol", "quantity", "entry_price"]
    rows = [["smith", "AAPL", 100, 150]]
    csv_path = _write_csv(tmp_path / "positions.csv", rows, header)

    portfolios = CSVPositionLoader(str(csv_path)).load()

    assert isinstance(portfolios["smith"].positions["AAPL"].instrument, Equity)


def test_loads_future_with_multiplier(tmp_path):
    header = ["pm", "symbol", "quantity", "entry_price", "product_type", "multiplier"]
    rows = [["smith", "ES=F", 2, 5000, "future", 50]]
    csv_path = _write_csv(tmp_path / "positions.csv", rows, header)

    portfolios = CSVPositionLoader(str(csv_path)).load()
    instrument = portfolios["smith"].positions["ES=F"].instrument

    assert isinstance(instrument, Future)
    assert instrument.multiplier == 50


def test_loads_option_with_full_metadata(tmp_path):
    header = ["pm", "symbol", "quantity", "entry_price", "product_type",
              "multiplier", "strike", "expiry", "option_type", "underlying"]
    rows = [["smith", "AAPL260717C00300000", 5, 8.5, "option",
              100, 300, "2026-07-17", "call", "AAPL"]]
    csv_path = _write_csv(tmp_path / "positions.csv", rows, header)

    portfolios = CSVPositionLoader(str(csv_path)).load()
    instrument = portfolios["smith"].positions["AAPL260717C00300000"].instrument

    assert isinstance(instrument, Option)
    assert instrument.strike == 300
    assert instrument.underlying == "AAPL"


def test_duplicate_symbol_for_same_pm_raises(tmp_path):
    header = ["pm", "symbol", "quantity", "entry_price"]
    rows = [
        ["smith", "AAPL", 100, 150],
        ["smith", "AAPL", 50, 140],
    ]
    csv_path = _write_csv(tmp_path / "positions.csv", rows, header)

    with pytest.raises(ValueError):
        CSVPositionLoader(str(csv_path)).load()
