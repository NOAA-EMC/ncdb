from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class AssetType:
    name: str
    description: Optional[str] = None
    id: Optional[int] = None

    @classmethod
    def from_orm(cls, orm: Any) -> AssetType:
        return cls(
            id=orm.id,
            name=orm.name,
            description=orm.description,
        )
