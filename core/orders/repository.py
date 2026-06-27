from core.orders.db import get_connection
from core.orders.order import Order


def insert_order(order):
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
    conn.commit()
    order.order_id = cursor.lastrowid
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