from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

from asset import Asset
from asset_context import AssetContext
from asset_source import AssetSource
from asset_type import AssetType

logger = logging.getLogger(__name__)


class BufrFilesystemDetector:
    """Filesystem detector that discovers BUFR files on disk and identifies their AssetType."""

    DEFAULT_RULES: Dict[str, str] = {
        "subpfl": "bufr_subpfl",
        "bathy": "bufr_bathy",
        "tesac": "bufr_tesac",
        "xbtctd": "bufr_xbtctd",
        "mbuoyb": "bufr_mbuoyb",
        "trkob": "bufr_trkob",
        "dbuoyb": "bufr_dbuoyb",
    }

    def discover(self, source: AssetSource) -> Iterable[str]:
        """Scans the source watch directory and yields candidate file URIs."""
        watch_dir_str = source.parameters.get("watch_dir")
        if not watch_dir_str:
            logger.warning(f"[BufrDetector] Source '{source.name}' missing 'watch_dir' parameter.")
            return []

        watch_dir = Path(watch_dir_str).resolve()
        if not watch_dir.exists():
            logger.warning(f"[BufrDetector] Watch directory does not exist for source '{source.name}': {watch_dir}")
            return []

        pattern = source.parameters.get("glob_pattern", "*.bufr_d")
        candidate_uris = []
        for file_path in watch_dir.glob(pattern):
            if file_path.is_file():
                candidate_uris.append(str(file_path.resolve()))

        return candidate_uris

    def identify(
        self,
        uri: str,
        source: AssetSource,
        asset_types_by_name: Dict[str, AssetType],
    ) -> Optional[Tuple[Asset, AssetContext]]:
        """Inspects URI candidate and returns (Asset, AssetContext) if recognized."""
        file_path = Path(uri)
        filename = file_path.name.lower()
        rules = source.parameters.get("rules", self.DEFAULT_RULES)

        for token, target_asset_type_name in rules.items():
            if token in filename:
                asset_type = asset_types_by_name.get(target_asset_type_name)
                if asset_type:
                    asset = Asset(uri=uri, asset_type=asset_type)
                    
                    # Construct initial context facts learned about candidate
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
