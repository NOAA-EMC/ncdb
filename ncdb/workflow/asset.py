from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

from asset_type import AssetType

logger = logging.getLogger(__name__)


@dataclass
class Asset:
    """Domain object representing a physical file or data stream."""

    uri: str
    asset_type: AssetType
    state: str = "AVAILABLE"
    fingerprint: Optional[str] = None
    id: Optional[int] = None

    @property
    def asset_type_id(self) -> int:
        return self.asset_type.id

    @property
    def asset_type_name(self) -> str:
        return self.asset_type.name

    @classmethod
    def from_orm(cls, asset_orm: Any) -> Asset:
        """Constructs an Asset domain object from an AssetORM instance."""
        return cls(
            id=asset_orm.id,
            uri=asset_orm.uri,
            asset_type=AssetType.from_orm(asset_orm.asset_type),
            state=asset_orm.state,
            fingerprint=asset_orm.fingerprint,
        )
