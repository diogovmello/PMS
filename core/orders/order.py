from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Order:
    pm: str
    symbol: str
    side: str
    quantity: float
    price: float
    timestamp: str = None
    status: str = "FILLED"
    order_id: int = None
    product_type: str = "equity"
    multiplier: float = None
    strike: float = None
    expiry: str = None
    option_type: str = None
    underlying: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.side not in ("buy", "sell"):
            raise ValueError(f"Invalid side: {self.side}")