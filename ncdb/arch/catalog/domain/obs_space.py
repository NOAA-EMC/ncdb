from dataclasses import dataclass


@dataclass(frozen=True)
class ObsSpace:
    id: int | None
    name: str
    description: str | None = None
