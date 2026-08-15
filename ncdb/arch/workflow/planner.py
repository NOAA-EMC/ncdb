from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .workflow import Workflow
    from .job import Job

logger = logging.getLogger(__name__)


class Planner:
    """Continuous background daemon that infers and enqueues missing jobs.
    
    Interacts strictly via the Workflow public domain interface.
    Has zero direct knowledge of SQL, database connections, or tables.
    """

    def __init__(self, workflow: Workflow, poll_interval: float = 2.0):
        self.workflow = workflow
        self.poll_interval = poll_interval

    def plan(self) -> List[Job]:
        """Performs a single evaluation pass and returns any newly created jobs."""
        new_jobs = []

        # 1. Fetch domain objects strictly through the Workflow interface
        assets = self.workflow.list_assets()
        transformations = self.workflow.list_transformations()
        existing_jobs = self.workflow.list_jobs()

        # Build index of existing work strictly by primary keys: (transformation_id, tuple(sorted(input_asset_ids)))
        existing_work = set()
        for j in existing_jobs:
            asset_ids_tuple = tuple(sorted(a.id for a in j.input_assets))
            existing_work.add((j.transformation_id, asset_ids_tuple))

        # Filter for AVAILABLE input assets
        available_assets = [a for a in assets if a.state == "AVAILABLE"]

        # 2. Match AVAILABLE assets against registered Transformations by AssetType ID
        for trans in transformations:
            required_type_ids = {at.id for at in trans.input_asset_types}

            # Single-input transformation matching
            if len(required_type_ids) == 1:
                target_type_id = next(iter(required_type_ids))
                # Match using primary key ID
                matching_assets = [a for a in available_assets if a.asset_type_id == target_type_id]

                for asset in matching_assets:
                    # Index work using transformation.id and asset.id
                    work_key = (trans.id, (asset.id,))

                    # If job doesn't exist yet, infer and create it
                    if work_key not in existing_work:
                        job = self.workflow.create_job(
                            transformation=trans,
                            input_assets=[asset]
                        )
                        new_jobs.append(job)
                        existing_work.add(work_key)

        return new_jobs

    def run_forever(self):
        """Infinite evaluation loop: Plan -> Sleep."""
        logger.info(f"[Planner] Starting continuous planner loop (poll_interval={self.poll_interval}s)...")
        try:
            while True:
                created_jobs = self.plan()
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            logger.info("[Planner] Planner loop stopped by user.")
