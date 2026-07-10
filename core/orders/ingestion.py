import csv
import os
from datetime import datetime, timezone

from core.orders.db import ROOT_DIR, get_connection
from core.orders.order import Order
from core.orders.repository import insert_order

INCOMING_DIR = str(ROOT_DIR / "data" / "incoming_orders")


def _is_processed(filename):
    conn = get_connection()
    row = conn.execute("SELECT 1 FROM processed_files WHERE filename = ?", (filename,)).fetchone()
    conn.close()
    return row is not None


def process_incoming_orders():
    """
    Each file's fills and its processed-marker are committed together in a
    single transaction, so a bad row partway through a file rolls back the
    whole file instead of leaving it half-inserted - re-running would
    otherwise re-insert the rows that already succeeded, since the file is
    only marked processed at the very end.
    """
    os.makedirs(INCOMING_DIR, exist_ok=True)
    processed_count = 0
    for filename in sorted(os.listdir(INCOMING_DIR)):
        if not filename.endswith(".csv") or _is_processed(filename):
            continue
        filepath = os.path.join(INCOMING_DIR, filename)
        conn = get_connection()
        try:
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
                    insert_order(order, conn=conn)
                    processed_count += 1
            conn.execute(
                "INSERT INTO processed_files (filename, processed_at) VALUES (?, ?)",
                (filename, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    return processed_count