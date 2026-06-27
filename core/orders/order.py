from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Order:
    """
    A single order record. For v1, every order is assumed fully filled at
    submission (status defaults to 'FILLED') - partial fills and order
    status transitions are a planned follow-up, not handled yet.
    """
    pm: str
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    price: float
    timestamp: str = None
    status: str = "FILLED"
    order_id: int = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.side not in ("buy", "sell"):
            raise ValueError(f"Invalid side: {self.side}")