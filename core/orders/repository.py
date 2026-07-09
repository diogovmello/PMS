from core.orders.db import get_connection
from core.orders.order import Order


def insert_order(order, conn=None):
    """
    Insert `order`. If `conn` is provided, the insert is left uncommitted
    on that connection so the caller can batch it into a larger transaction
    (see `core.orders.ingestion`); otherwise it's committed immediately on
    a connection of its own.
    """
    owns_conn = conn is None
    if owns_conn:
        conn = get_connection()

    cursor = conn.execute(
        """
        INSERT INTO orders (pm, symbol, side, quantity, price, timestamp, status,
                             product_type, multiplier, strike, expiry, option_type, underlying)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (order.pm, order.symbol, order.side, order.quantity, order.price,
         order.timestamp, order.status, order.product_type, order.multiplier,
         order.strike, order.expiry, order.option_type, order.underlying),
    )
    order.order_id = cursor.lastrowid

    if owns_conn:
        conn.commit()
        conn.close()
    return order


def _row_to_order(row):
    return Order(
        pm=row["pm"],
        symbol=row["symbol"],
        side=row["side"],
        quantity=row["quantity"],
        price=row["price"],
        timestamp=row["timestamp"],
        status=row["status"],
        order_id=row["order_id"],
        product_type=row["product_type"],
        multiplier=row["multiplier"],
        strike=row["strike"],
        expiry=row["expiry"],
        option_type=row["option_type"],
        underlying=row["underlying"],
    )


def get_orders_by_pm(pm):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM orders WHERE pm = ?", (pm,)).fetchall()
    conn.close()
    return [_row_to_order(row) for row in rows]


def get_all_orders():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM orders").fetchall()
    conn.close()
    return [_row_to_order(row) for row in rows]