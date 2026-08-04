from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from asset_type import AssetType


@dataclass
class Asset:
    """Domain object representing a physical or logical data asset."""

    id: int
    uri: str
    asset_type_id: int
    state: str = "AVAILABLE"
    asset_type: Optional[AssetType] = None

    @property
    def asset_type_name(self) -> Optional[str]:
        """Convenience accessor for the name of the asset type."""
        return self.asset_type.name if self.asset_type else None

    @classmethod
    def from_orm(cls, asset_orm: Any) -> Asset:
        """Constructs an Asset domain object from an AssetORM instance."""
        asset_type_domain = None
        if hasattr(asset_orm, "asset_type") and asset_orm.asset_type:
            asset_type_domain = AssetType.from_orm(asset_orm.asset_type)

        return cls(
            id=asset_orm.id,
            uri=asset_orm.uri,
            asset_type_id=asset_orm.asset_type_id,
            state=asset_orm.state,
            asset_type=asset_type_domain,
        )

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, type='{self.asset_type_name}', uri='{self.uri}')>"
