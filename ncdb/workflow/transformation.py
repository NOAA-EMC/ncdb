from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from asset_type import AssetType

@dataclass
class Transformation:
    name: str
    handler: str
    input_asset_types: List[AssetType]
    output_asset_types: List[AssetType]
    parameters: Optional[Dict[str, Any]] = None
    id: Optional[int] = None

    @classmethod
    def from_orm(cls, orm: Any) -> Transformation:
        raw_params = orm.parameters
        if isinstance(raw_params, str) and raw_params.strip():
            try:
                params = json.loads(raw_params)
            except Exception:
                params = {}
        else:
            params = raw_params or {}

        inputs = [AssetType.from_orm(i.asset_type) for i in orm.inputs if i.asset_type]
        outputs = [AssetType.from_orm(o.asset_type) for o in orm.outputs if o.asset_type]

        return cls(
            id=orm.id,
            name=orm.name,
            handler=orm.handler,
            input_asset_types=inputs,
            output_asset_types=outputs,
            parameters=params,
        )
