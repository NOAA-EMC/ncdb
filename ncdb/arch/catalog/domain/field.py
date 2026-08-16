from dataclasses import dataclass


@dataclass(frozen=True)
class Field:
    id: int | None
    name: str
    description: str | None = None
