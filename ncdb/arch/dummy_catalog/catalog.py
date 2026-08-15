from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from workflow.asset import Asset
    from workflow.asset_context import AssetContext

logger = logging.getLogger(__name__)


class Catalog:
    """
    Dummy in-memory Catalog implementation.

    This is a temporary implementation used to decouple
    the Sensor from the Workflow package.
    """

    def __init__(self):
        self._entries: dict[
            str,
            tuple[Asset, AssetContext],
        ] = {}

    def register(
        self,
        asset: Asset,
        context: AssetContext,
    ) -> None:
        self._entries[asset.uri] = (asset, context)

        logger.info(
            f"[Catalog] Registered context for "
            f"'{asset.uri}' "
            f"(keys={list(context.data.keys())})"
        )

    def get_context(
        self,
        uri: str,
    ) -> AssetContext | None:
        entry = self._entries.get(uri)
        return entry[1] if entry else None
