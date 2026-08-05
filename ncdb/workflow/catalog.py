from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from asset import Asset
    from asset_context import AssetContext

logger = logging.getLogger(__name__)


class Catalog:
    """Abstract/Initial implementation of the Observation Catalog.
    
    Cares about the scientific meaning and metadata of assets.
    """

    def __init__(self):
        # Initial in-memory registry: asset.uri -> (asset, context)
        self._entries: Dict[str, tuple[Asset, AssetContext]] = {}

    def register(self, asset: Asset, context: AssetContext) -> None:
        """Registers an asset and its discovered context into the catalog."""
        self._entries[asset.uri] = (asset, context)
        logger.info(
            f"[Catalog] Registered context for '{asset.uri}' "
            f"(keys={list(context.data.keys())})"
        )

    def get_context(self, uri: str) -> AssetContext | None:
        """Retrieves stored context for an asset URI."""
        entry = self._entries.get(uri)
        return entry[1] if entry else None
