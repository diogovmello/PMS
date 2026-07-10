import pytest

from core.orders.order import Order
from core.orders.repository import insert_order, get_orders_by_pm, get_all_orders
import core.orders.ingestion as ingestion


def _write_csv(path, rows, header):
    lines = [",".join(header)]
    lines += [",".join(str(v) for v in row) for row in rows]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


class TestOrder:
    def test_defaults_status_to_filled(self):
        order = Order(pm="smith", symbol="AAPL", side="buy", quantity=10, price=100)
        assert order.status == "FILLED"

    def test_auto_generates_timestamp_when_not_given(self):
        order = Order(pm="smith", symbol="AAPL", side="buy", quantity=10, price=100)
        assert order.timestamp is not None

    def test_keeps_explicit_timestamp(self):
        order = Order(pm="smith", symbol="AAPL", side="buy", quantity=10, price=100,
                       timestamp="2026-01-01T00:00:00+00:00")
        assert order.timestamp == "2026-01-01T00:00:00+00:00"

    def test_invalid_side_raises(self):
        with pytest.raises(ValueError):
            Order(pm="smith", symbol="AAPL", side="hold", quantity=10, price=100)


class TestRepository:
    def test_insert_and_get_all_orders(self, temp_orders_db):
        insert_order(Order(pm="smith", symbol="AAPL", side="buy", quantity=10, price=100))
        insert_order(Order(pm="jones", symbol="TSLA", side="buy", quantity=5, price=700))

        all_orders = get_all_orders()
        assert len(all_orders) == 2
        assert {o.symbol for o in all_orders} == {"AAPL", "TSLA"}

    def test_get_orders_by_pm_filters(self, temp_orders_db):
        insert_order(Order(pm="smith", symbol="AAPL", side="buy", quantity=10, price=100))
        insert_order(Order(pm="jones", symbol="TSLA", side="buy", quantity=5, price=700))

        smith_orders = get_orders_by_pm("smith")
        assert len(smith_orders) == 1
        assert smith_orders[0].symbol == "AAPL"

    def test_insert_order_assigns_order_id(self, temp_orders_db):
        order = insert_order(Order(pm="smith", symbol="AAPL", side="buy", quantity=10, price=100))
        assert order.order_id is not None


class TestIngestion:
    def test_processes_new_file_and_marks_it_processed(self, temp_orders_db, tmp_path, monkeypatch):
        incoming_dir = tmp_path / "incoming"
        monkeypatch.setattr(ingestion, "INCOMING_DIR", str(incoming_dir))
        incoming_dir.mkdir()
        _write_csv(
            incoming_dir / "orders_1.csv",
            [["smith", "AAPL", "buy", 10, 100]],
            ["pm", "symbol", "side", "quantity", "price"],
        )

        processed_count = ingestion.process_incoming_orders()

        assert processed_count == 1
        assert len(get_all_orders()) == 1

    def test_reprocessing_skips_already_processed_files(self, temp_orders_db, tmp_path, monkeypatch):
        incoming_dir = tmp_path / "incoming"
        monkeypatch.setattr(ingestion, "INCOMING_DIR", str(incoming_dir))
        incoming_dir.mkdir()
        _write_csv(
            incoming_dir / "orders_1.csv",
            [["smith", "AAPL", "buy", 10, 100]],
            ["pm", "symbol", "side", "quantity", "price"],
        )

        first_run = ingestion.process_incoming_orders()
        second_run = ingestion.process_incoming_orders()

        assert first_run == 1
        assert second_run == 0
        assert len(get_all_orders()) == 1  # not duplicated

    def test_bad_row_rolls_back_whole_file_and_leaves_it_unprocessed(self, temp_orders_db, tmp_path, monkeypatch):
        incoming_dir = tmp_path / "incoming"
        monkeypatch.setattr(ingestion, "INCOMING_DIR", str(incoming_dir))
        incoming_dir.mkdir()
        _write_csv(
            incoming_dir / "orders_1.csv",
            [
                ["smith", "AAPL", "buy", 10, 100],   # good row, would insert if committed
                ["smith", "MSFT", "hold", 5, 300],   # invalid side - raises in Order()
            ],
            ["pm", "symbol", "side", "quantity", "price"],
        )

        with pytest.raises(ValueError):
            ingestion.process_incoming_orders()

        # the good row from the same file must not have been left committed
        assert get_all_orders() == []

        # file wasn't marked processed, so a corrected re-run can pick it up
        assert not ingestion._is_processed("orders_1.csv")
