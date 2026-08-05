from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class AssetSource:
    """Domain object representing an external storage watch location and detector binding."""

    name: str
    handler: str
    parameters: Dict[str, Any]
    id: Optional[int] = None

    @classmethod
    def from_orm(cls, source_orm: Any) -> AssetSource:
        """Constructs an AssetSource domain object from an AssetSourceORM instance."""
        raw_params = source_orm.parameters
        if isinstance(raw_params, str) and raw_params.strip():
            try:
                params = json.loads(raw_params)
            except Exception:
                params = {}
        else:
            params = raw_params or {}

        return cls(
            id=source_orm.id,
            name=source_orm.name,
            handler=source_orm.handler,
            parameters=params,
        )
