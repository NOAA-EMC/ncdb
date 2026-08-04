from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class AssetType:
    """Domain object representing a category/format of asset in the catalog."""

    id: int
    name: str
    description: Optional[str] = None

    @classmethod
    def from_orm(cls, asset_type_orm: Any) -> AssetType:
        """Constructs an AssetType domain object from an AssetTypeORM instance."""
        return cls(
            id=asset_type_orm.id,
            name=asset_type_orm.name,
            description=asset_type_orm.description,
        )

    def __repr__(self) -> str:
        return f"<AssetType(id={self.id}, name='{self.name}')>"
