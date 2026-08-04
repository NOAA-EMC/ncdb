from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from workflow import Workflow
    from asset_type import AssetType
    from asset import Asset

logger = logging.getLogger(__name__)


# ==============================================================================
# PROTOTYPE DETECTION BOUNDARY (PROPOSED FOR FUTURE REFACTORING)
# ==============================================================================
# TODO: Replace this hardcoded mapping table with database-driven detection rules
# stored on AssetType (e.g. storage_scheme, detector_type, detector_rule).
HARDCODED_BUFR_TYPE_RULES: Dict[str, str] = {
    "subpfl": "bufr_subpfl",
    "bathy": "bufr_bathy",
    "tesac": "bufr_tesac",
    "xbtctd": "bufr_xbtctd",
    "mbuoyb": "bufr_mbuoyb",
    "trkob": "bufr_trkob",
    "dbuoyb": "bufr_dbuoyb",
}
# ==============================================================================


class Sensor:
    """Watches a directory for incoming BUFR files and registers them."""

    def __init__(self, watch_dir: str | Path, workflow: Workflow):
        self.watch_dir = Path(watch_dir).resolve()
        self.workflow = workflow

    def detect_asset_type(self, file_path: Path, asset_types_by_name: Dict[str, AssetType]) -> Optional[AssetType]:
        """Detects AssetType domain object from filename pattern."""
        filename = file_path.name.lower()

        for token, asset_type_name in HARDCODED_BUFR_TYPE_RULES.items():
            if token in filename:
                return asset_types_by_name.get(asset_type_name)

        return None

    def scan(self) -> List[Path]:
        """Finds unregistered files in watch_dir."""
        if not self.watch_dir.exists():
            logger.warning(f"[Sensor] Watch directory does not exist: {self.watch_dir}")
            return []

        # Get set of all currently registered URIs in DB
        known_uris = {a.uri for a in self.workflow.list_assets()}
        new_files = []

        for file_path in self.watch_dir.glob("*.bufr_d"):
            if file_path.is_file() and str(file_path.resolve()) not in known_uris:
                new_files.append(file_path)

        return new_files

    def run_forever(self, interval: float = 3.0):
        """Continuously watches directory and registers new files."""
        logger.info(f"[Sensor] Monitoring directory '{self.watch_dir}' (interval={interval}s)...")
        try:
            while True:
                # Fetch registered AssetType domain objects from Workflow
                registered_asset_types = self.workflow.list_asset_types()
                asset_types_by_name = {at.name: at for at in registered_asset_types}

                for file_path in self.scan():
                    asset_type = self.detect_asset_type(file_path, asset_types_by_name)
                    
                    if asset_type:
                        uri = str(file_path.resolve())
                        try:
                            # Pass domain AssetType directly
                            asset: Asset = self.workflow.register_asset(uri=uri, asset_type=asset_type)
                            logger.info(f"[Sensor] Registered '{file_path.name}' as Asset #{asset.id} ('{asset.asset_type_name}')")
                        except Exception as e:
                            logger.error(f"[Sensor] Failed to register asset '{uri}': {e}")
                    else:
                        pass

                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("[Sensor] Directory watcher loop stopped by user.")
