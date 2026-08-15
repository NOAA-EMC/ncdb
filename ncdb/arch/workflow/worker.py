from __future__ import annotations

import importlib
import logging
import time
from typing import Callable, Optional, TYPE_CHECKING

from .job import Job

if TYPE_CHECKING:
    from .workflow import Workflow

logger = logging.getLogger(__name__)


class Worker:
    def __init__(self, workflow: Workflow, poll_interval: float = 2.0):
        self.workflow = workflow
        self.poll_interval = poll_interval

    def _resolve_handler(self, handler_str: str) -> Callable:
        """Dynamically loads module:function from a string."""
        handler_str = handler_str.replace("/", ".").replace("\\", ".")
        if ":" not in handler_str:
            raise ValueError(f"Invalid handler format '{handler_str}'. Expected 'module:function'.")
        
        mod_name, func_name = handler_str.split(":", 1)
        module = importlib.import_module(mod_name)
        return getattr(module, func_name)

    def execute(self, job: Job) -> bool:
        """Executes a single job by invoking its designated handler function."""
        self.workflow.mark_job_running(job.id)

        try:
            # 1. Resolve the handler target (e.g. 'adapter:run_b2i_converter')
            handler_func = self._resolve_handler(job.handler)

            # 2. Invoke handler passing the Job domain object directly
            output_uris, output_asset_type = handler_func(job)

            # 3. Report completion back to workflow engine passing domain AssetType
            self.workflow.mark_job_success(
                job_id=job.id,
                output_uris=output_uris,
                output_asset_type=output_asset_type
            )
            logger.info(f"[Worker] Job {job.id} completed successfully.")
            return True

        except Exception as e:
            logger.exception(f"[Worker] Job {job.id} failed: {e}")
            self.workflow.mark_job_failed(job.id, error_log=str(e))
            return False

    def run_once(self) -> bool:
        """Attempts to claim and execute a single pending job if available."""
        job = self.workflow.claim_job()
        if job:
            self.execute(job)
            return True
        return False

    def run_forever(self):
        """Continuous worker daemon loop: Claim -> Execute -> Sleep."""
        logger.info(f"[Worker] Starting continuous worker loop (poll_interval={self.poll_interval}s)...")
        try:
            while True:
                executed = self.run_once()
                if not executed:
                    time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            logger.info("[Worker] Worker loop stopped by user.")
