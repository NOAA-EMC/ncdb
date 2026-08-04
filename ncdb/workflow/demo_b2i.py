import logging
import multiprocessing
import time
from pathlib import Path

from workflow import Workflow
from worker import Worker
from planner import Planner
from sensor import Sensor
from workflow_definitions import register_all_b2i_converters

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
# Silence verbose third-party loggers
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger("demo_b2i")

BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = BASE_DIR / "obsforge-workflow.db"
OBSFORGE_DIR = "/scratch3/NCEPDEV/da/Edward.Givelberg/obsForge"
BUFR_DATA_DIR = "/scratch3/NCEPDEV/da/common/ci/bufr"


# --- Process 1: Sensor Process ---
def run_sensor_process(db_path: str, bufr_dir: str):
    """Directory monitoring daemon process."""
    logger.info("[Sensor Process] Started.")
    wf = Workflow(db_path)
    sensor = Sensor(watch_dir=bufr_dir, workflow=wf)
    sensor.run_forever(interval=3.0)


# --- Process 2: Planner Daemon Process ---
def run_planner_process(db_path: str):
    """Planner background daemon."""
    logger.info("[Planner Process] Started.")
    wf = Workflow(db_path)
    planner = Planner(workflow=wf, poll_interval=2.0)
    planner.run_forever()


# --- Process 3: Worker Daemon Process ---
def run_worker_process(db_path: str):
    """Worker background daemon."""
    logger.info("[Worker Process] Started.")
    wf = Workflow(db_path)
    worker = Worker(workflow=wf, poll_interval=2.0)
    worker.run_forever()


# --- Main Orchestrator ---
def main():
    workflow = Workflow(str(DB_PATH))
    logger.info("Initializing Workflow DB and Converter Definitions...")

    # Register all 14 Converters and Asset Types in database
    register_all_b2i_converters(
        workflow=workflow,
        obsforge_dir=OBSFORGE_DIR,
        platform_module="ursa.intel",
        output_base_dir=BASE_DIR / "ioda_data"
    )

    p_sensor = multiprocessing.Process(
        target=run_sensor_process, 
        args=(str(DB_PATH), BUFR_DATA_DIR), 
        name="Sensor"
    )
    p_planner = multiprocessing.Process(
        target=run_planner_process, 
        args=(str(DB_PATH),), 
        name="Planner"
    )
    p_worker = multiprocessing.Process(
        target=run_worker_process, 
        args=(str(DB_PATH),), 
        name="Worker"
    )

    logger.info("--- Starting System Processes (Sensor, Planner, Worker) ---")
    p_sensor.start()
    p_planner.start()
    p_worker.start()

    try:
        p_sensor.join()
        p_planner.join()
        p_worker.join()
    except KeyboardInterrupt:
        logger.info("\n--- Shutting down system processes ---")
        p_sensor.terminate()
        p_planner.terminate()
        p_worker.terminate()
        p_sensor.join()
        p_planner.join()
        p_worker.join()
        logger.info("System stopped.")


if __name__ == "__main__":
    main()
