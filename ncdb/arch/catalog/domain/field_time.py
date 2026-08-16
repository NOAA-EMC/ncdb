from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FieldTime:
    id: int | None
    field_id: int
    time: datetime
    data_product_id: int
