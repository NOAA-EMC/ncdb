import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
# Silence verbose third-party loggers
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger("demo_b2i")

import multiprocessing
import time
from pathlib import Path

from workflow import (
    Workflow, 
    Worker, 
    Planner, 
    AssetSource
)
# from sensor import Sensor
from sensor import DataProcessor
# from dummy_catalog import Catalog
from catalog import Catalog
from obsforge.b2i import register_all_b2i_converters
from datastore import DataStore
from datastore.devices.filesystem import FileSystemDevice


BASE_DIR = Path(__file__).parent.resolve()

WORKFLOW_DB_PATH = BASE_DIR / "obsforge-workflow.db"
CATALOG_DB_PATH = BASE_DIR / "obsforge-catalog.db"
DATASTORE_DB_PATH = BASE_DIR / "obsforge-datastore.db"

OBSFORGE_DIR = "/scratch3/NCEPDEV/da/Edward.Givelberg/obsForge"
BUFR_DATA_DIR = "/scratch3/NCEPDEV/da/common/ci/bufr"


# def run_sensor_process(
    # workflow_db_path: str,
    # catalog_db_path: str,
# ):
    # logger.info("[Sensor Process] Started.")
# 
    # wf = Workflow(workflow_db_path)
    # catalog = Catalog(catalog_db_path)
# 
    # sensor = Sensor(
        # workflow=wf,
        # catalog=catalog,
    # )
# 
    # sensor.run_forever(interval=3.0)


def run_data_processor_process(
    workflow_db_path: str,
    catalog_db_path: str,
):
    logger.info("[Data Processor Process] Started.")

    wf = Workflow(workflow_db_path)
    catalog = Catalog(catalog_db_path)

    processor = DataProcessor(
        workflow=wf,
        catalog=catalog,
    )

    processor.run_forever(interval=3.0)

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

def init_catalog():
    catalog = Catalog(str(CATALOG_DB_PATH))

    temperature = catalog.register_variable(
        "temperature",
        "Sea water temperature",
    )

    salinity = catalog.register_variable(
        "salinity",
        "Sea water salinity",
    )

    profile = catalog.register_obs_space(
        "ocean_profile",
        "Ocean profile observations",
    )

    catalog.associate(profile, temperature)
    catalog.associate(profile, salinity)

    return catalog

def init_workflow():
    workflow = Workflow(str(WORKFLOW_DB_PATH))
    logger.info("Initializing Workflow DB and Converter Definitions...")

    # Register default AssetSource for BUFR files
    workflow.register_asset_source(
        AssetSource(
            name="bufr_directory_source",
            handler="obsforge.detectors.bufr:BufrFilesystemDetector",
            parameters={
                "watch_dir": BUFR_DATA_DIR,
                "glob_pattern": "*.bufr_d"
            }
        )
    )

    # Register all 14 Converters and Asset Types in database
    register_all_b2i_converters(
        workflow=workflow,
        obsforge_dir=OBSFORGE_DIR,
        platform_module="ursa.intel",
        output_base_dir=BASE_DIR / "ioda_data"
    )

    return workflow

def init_datastore():
    datastore = DataStore(str(DATASTORE_DB_PATH))

    device = FileSystemDevice(
        BASE_DIR / "datastore_files"
    )

    datastore.register_device(
        "filesystem",
        device,
    )

    return datastore


def main():
    catalog = init_catalog()
    workflow = init_workflow()
    datastore = init_datastore()

    # p_sensor = multiprocessing.Process(
        # target=run_sensor_process,
        # args=(
            # str(WORKFLOW_DB_PATH),
            # str(CATALOG_DB_PATH),
        # ),
        # name="Sensor",
    # )

    p_processor = multiprocessing.Process(
        target=run_data_processor_process,
        args=(
            str(WORKFLOW_DB_PATH),
            str(CATALOG_DB_PATH),
        ),
        name="DataProcessor",
    )

    p_planner = multiprocessing.Process(
        target=run_planner_process, 
        args=(str(WORKFLOW_DB_PATH),), 
        name="Planner"
    )
    p_worker = multiprocessing.Process(
        target=run_worker_process, 
        args=(str(WORKFLOW_DB_PATH),), 
        name="Worker"
    )

    logger.info("--- Starting System Processes (Sensor, Planner, Worker) ---")
    p_processor.start()
    # p_sensor.start()
    p_planner.start()
    p_worker.start()

    try:
        p_processor.join()
        # p_sensor.join()
        p_planner.join()
        p_worker.join()
    except KeyboardInterrupt:
        logger.info("\n--- Shutting down system processes ---")
        # p_sensor.terminate()
        p_processor.terminate()
        p_planner.terminate()
        p_worker.terminate()
        p_processor.join()
        # p_sensor.join()
        p_planner.join()
        p_worker.join()
        logger.info("System stopped.")


if __name__ == "__main__":
    main()
