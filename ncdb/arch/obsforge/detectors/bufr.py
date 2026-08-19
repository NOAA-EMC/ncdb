from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

from workflow import (
    Asset,
    AssetContext,
    AssetType,
)
from sensor import AssetSource

logger = logging.getLogger(__name__)


class BufrFilesystemDetector:
    """Detects BUFR files on a filesystem."""

    DEFAULT_RULES: Dict[str, str] = {
        "subpfl": "bufr_subpfl",
        "bathy": "bufr_bathy",
        "tesac": "bufr_tesac",
        "xbtctd": "bufr_xbtctd",
        "mbuoyb": "bufr_mbuoyb",
        "trkob": "bufr_trkob",
        "dbuoyb": "bufr_dbuoyb",
    }

    def __init__(
        self,
        asset_types: Iterable[AssetType],
    ) -> None:
        self.asset_types_by_name = {
            asset_type.name: asset_type
            for asset_type in asset_types
        }

    def discover(self, source: AssetSource) -> Iterable[str]:
        """Scans the source watch directory and yields candidate URIs."""

        watch_dir_str = source.parameters.get("watch_dir")
        if not watch_dir_str:
            logger.warning(
                f"[BufrDetector] Source '{source.name}' "
                "missing 'watch_dir' parameter."
            )
            return []

        watch_dir = Path(watch_dir_str).resolve()

        if not watch_dir.exists():
            logger.warning(
                f"[BufrDetector] Watch directory does not exist "
                f"for source '{source.name}': {watch_dir}"
            )
            return []

        pattern = source.parameters.get(
            "glob_pattern",
            "*.bufr_d",
        )

        return [
            str(path.resolve())
            for path in watch_dir.glob(pattern)
            if path.is_file()
        ]

    def identify(
        self,
        uri: str,
        source: AssetSource,
    ) -> Optional[Tuple[Asset, AssetContext]]:
        """Identifies a candidate and returns (Asset, AssetContext)."""

        file_path = Path(uri)
        filename = file_path.name.lower()

        rules = source.parameters.get(
            "rules",
            self.DEFAULT_RULES,
        )

        for token, asset_type_name in rules.items():

            if token not in filename:
                continue

            asset_type = self.asset_types_by_name.get(
                asset_type_name
            )

            if asset_type is None:
                logger.warning(
                    f"[BufrDetector] Unknown AssetType "
                    f"'{asset_type_name}' for '{uri}'"
                )
                return None

            asset = Asset(
                uri=uri,
                asset_type=asset_type,
            )

            context = AssetContext(
                data={
                    "source_name": source.name,
                    "filename": file_path.name,
                    "format_token": token,
                    "discovered_at": time.time(),
                }
            )

            return asset, context

        return None
