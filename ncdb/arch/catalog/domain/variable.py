from dataclasses import dataclass


@dataclass(frozen=True)
class Variable:
    id: int | None
    name: str
    description: str | None = None
