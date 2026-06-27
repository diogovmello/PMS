from core.orders.db import get_connection
from core.orders.order import Order


def insert_order(order):
    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO orders (pm, symbol, side, quantity, price, timestamp, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (order.pm, order.symbol, order.side, order.quantity, order.price,
         order.timestamp, order.status),
    )
    conn.commit()
    order_id = cursor.lastrowid
    conn.close()
    return order_id


def get_orders_by_pm(pm):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM orders WHERE pm = ? ORDER BY timestamp", (pm,)
    ).fetchall()
    conn.close()
    return [_row_to_order(row) for row in rows]


def get_all_orders():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM orders ORDER BY timestamp").fetchall()
    conn.close()
    return [_row_to_order(row) for row in rows]


def _row_to_order(row):
    return Order(
        order_id=row["order_id"], pm=row["pm"], symbol=row["symbol"],
        side=row["side"], quantity=row["quantity"], price=row["price"],
        timestamp=row["timestamp"], status=row["status"],
    )