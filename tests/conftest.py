import pytest

import core.orders.db as db


@pytest.fixture
def temp_orders_db(tmp_path, monkeypatch):
    """
    Points the orders DB at a throwaway sqlite file for the duration of the
    test, so tests never touch the real data/orders.db.
    """
    db_path = str(tmp_path / "orders.db")
    monkeypatch.setattr(db, "DB_PATH", db_path)
    db.init_db()
    return db_path
