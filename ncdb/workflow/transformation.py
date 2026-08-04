from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from asset_type import AssetType


class Transformation:
    """Domain object representing a transformation pipeline step."""

    def __init__(
        self,
        id: int,
        name: str,
        handler: str,
        input_asset_types: List[AssetType],
        output_asset_types: List[AssetType],
        parameters: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.name = name
        self.handler = handler
        self.input_asset_types = input_asset_types
        self.output_asset_types = output_asset_types
        self.parameters = parameters or {}

    @property
    def input_type_names(self) -> List[str]:
        """Convenience property returning names of input asset types."""
        return [at.name for at in self.input_asset_types]

    @property
    def output_type_names(self) -> List[str]:
        """Convenience property returning names of output asset types."""
        return [at.name for at in self.output_asset_types]

    @classmethod
    def from_orm(cls, transformation_orm: Any) -> Transformation:
        """Constructs a Transformation domain object from an ORM instance.
        
        Assumes transformation_orm has inputs and outputs eager-loaded.
        """
        raw_params = transformation_orm.parameters
        if isinstance(raw_params, str) and raw_params.strip():
            try:
                params = json.loads(raw_params)
            except json.JSONDecodeError:
                params = {}
        elif isinstance(raw_params, dict):
            params = raw_params
        else:
            params = {}

        input_asset_types = [
            AssetType.from_orm(ti.asset_type)
            for ti in transformation_orm.inputs
            if ti.asset_type is not None
        ]
        output_asset_types = [
            AssetType.from_orm(to.asset_type)
            for to in transformation_orm.outputs
            if to.asset_type is not None
        ]

        return cls(
            id=transformation_orm.id,
            name=transformation_orm.name,
            handler=transformation_orm.handler,
            input_asset_types=input_asset_types,
            output_asset_types=output_asset_types,
            parameters=params,
        )

    def __repr__(self) -> str:
        return (
            f"<Transformation(id={self.id}, name='{self.name}', "
            f"inputs={self.input_type_names}, outputs={self.output_type_names})>"
        )
