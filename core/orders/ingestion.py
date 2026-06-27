import csv
import os
from datetime import datetime, timezone

from core.orders.db import get_connection
from core.orders.order import Order
from core.orders.repository import insert_order

INCOMING_DIR = "data/incoming_orders"


def _is_processed(filename):
    conn = get_connection()
    row = conn.execute("SELECT 1 FROM processed_files WHERE filename = ?", (filename,)).fetchone()
    conn.close()
    return row is not None


def _mark_processed(filename):
    conn = get_connection()
    conn.execute(
        "INSERT INTO processed_files (filename, processed_at) VALUES (?, ?)",
        (filename, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def process_incoming_orders():
    os.makedirs(INCOMING_DIR, exist_ok=True)
    processed_count = 0
    for filename in sorted(os.listdir(INCOMING_DIR)):
        if not filename.endswith(".csv") or _is_processed(filename):
            continue
        filepath = os.path.join(INCOMING_DIR, filename)
        with open(filepath, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                order = Order(
                    pm=row["pm"],
                    symbol=row["symbol"],
                    side=row["side"].lower(),
                    quantity=float(row["quantity"]),
                    price=float(row["price"]),
                    product_type=row.get("product_type") or "equity",
                    multiplier=float(row["multiplier"]) if row.get("multiplier") else None,
                    strike=float(row["strike"]) if row.get("strike") else None,
                    expiry=row.get("expiry") or None,
                    option_type=row.get("option_type") or None,
                    underlying=row.get("underlying") or None,
                )
                insert_order(order)
                processed_count += 1
        _mark_processed(filename)
    return processed_count