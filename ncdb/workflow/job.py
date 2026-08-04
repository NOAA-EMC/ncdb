from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from asset import Asset
from transformation import Transformation

logger = logging.getLogger(__name__)


class Job:
    """Domain object representing a concrete execution unit of a Transformation."""

    def __init__(
        self,
        id: int,
        transformation: Transformation,
        input_assets: List[Asset],
        output_assets: Optional[List[Asset]] = None,
        state: str = "PENDING",
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
        error_log: Optional[str] = None,
    ):
        self.id = id
        self.transformation = transformation
        self.input_assets = input_assets
        self.output_assets = output_assets or []
        self.state = state
        self.started_at = started_at
        self.finished_at = finished_at
        self.error_log = error_log

    @property
    def transformation_id(self) -> int:
        return self.transformation.id

    @property
    def transformation_name(self) -> str:
        return self.transformation.name

    @property
    def handler(self) -> str:
        return self.transformation.handler

    @property
    def parameters(self) -> Dict[str, Any]:
        return self.transformation.parameters

    @property
    def input_asset_uris(self) -> List[str]:
        """Convenience accessor for physical URIs required by adapters."""
        return [a.uri for a in self.input_assets]

    @property
    def output_asset_uris(self) -> List[str]:
        """Convenience accessor for physical output URIs."""
        return [a.uri for a in self.output_assets]

    @classmethod
    def from_orm(cls, job_orm: Any) -> Job:
        """Constructs a Job domain object from a JobORM instance with loaded relationships."""
        transformation = Transformation.from_orm(job_orm.transformation)

        input_assets = [
            Asset.from_orm(jia.asset)
            for jia in job_orm.job_input_assets
            if jia.asset is not None
        ]
        output_assets = [
            Asset.from_orm(joa.asset)
            for joa in job_orm.job_output_assets
            if joa.asset is not None
        ]

        return cls(
            id=job_orm.id,
            transformation=transformation,
            input_assets=input_assets,
            output_assets=output_assets,
            state=job_orm.state,
            started_at=job_orm.started_at,
            finished_at=job_orm.finished_at,
            error_log=job_orm.error_log,
        )

    def __repr__(self) -> str:
        return (
            f"<Job(id={self.id}, transformation='{self.transformation_name}', "
            f"state='{self.state}', input_assets={self.input_assets})>"
        )
