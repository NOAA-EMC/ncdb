from __future__ import annotations

import importlib
import logging
import time
from typing import TYPE_CHECKING, Any, Dict, Optional

from asset import Asset
from asset_context import AssetContext

if TYPE_CHECKING:
    from workflow import Workflow
    from catalog import Catalog
    from asset_source import AssetSource

logger = logging.getLogger(__name__)


def load_handler(handler_str: str) -> Any:
    """Loads a detector class/callable from a string (module.path:ClassName or module:ClassName)."""
    if ":" not in handler_str:
        raise ValueError(f"Invalid handler string '{handler_str}'. Expected 'module:Class'")
    module_path, class_name = handler_str.split(":", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


class Sensor:
    """Orchestrates asset discovery and identification across configured AssetSources,
    registering physical assets with Workflow and scientific context with Catalog.
    """

    def __init__(self, workflow: Workflow, catalog: Optional[Catalog] = None):
        self.workflow = workflow
        
        if catalog is None:
            from catalog import Catalog as MemoryCatalog
            self.catalog = MemoryCatalog()
        else:
            self.catalog = catalog

        self._detector_cache: Dict[str, Any] = {}

    def _resolve_detector(self, source: AssetSource) -> Any:
        """Resolves detector instance based on source.handler."""
        handler_str = source.handler

        if handler_str not in self._detector_cache:
            detector_cls = load_handler(handler_str)
            if isinstance(detector_cls, type):
                self._detector_cache[handler_str] = detector_cls()
            else:
                self._detector_cache[handler_str] = detector_cls

        return self._detector_cache[handler_str]

    def run_once(self):
        """Scans all AssetSources, identifies new candidates, and registers with Workflow and Catalog."""
        sources = self.workflow.list_asset_sources()
        if not sources:
            logger.debug("[Sensor] No AssetSources registered in workflow.")
            return

        registered_asset_types = self.workflow.list_asset_types()
        asset_types_by_name = {at.name: at for at in registered_asset_types}
        known_uris = {a.uri for a in self.workflow.list_assets()}

        for source in sources:
            try:
                detector = self._resolve_detector(source)
            except Exception as e:
                logger.error(f"[Sensor] Failed to resolve handler '{source.handler}' for source '{source.name}': {e}")
                continue

            try:
                candidate_uris = detector.discover(source)
            except Exception as e:
                logger.error(f"[Sensor] Discovery failed for source '{source.name}': {e}")
                continue

            for uri in candidate_uris:
                if uri in known_uris:
                    continue

                try:
                    result = detector.identify(uri, source, asset_types_by_name)
                    if result:
                        asset, context = result

                        # 1. Register with Workflow Execution Engine
                        registered_asset = self.workflow.register_asset(asset)
                        known_uris.add(uri)

                        # 2. Register with Scientific Observation Catalog
                        self.catalog.register(registered_asset, context)

                        logger.info(
                            f"[Sensor] [{source.name}] Registered '{registered_asset.uri}' "
                            f"as Asset #{registered_asset.id} ('{registered_asset.asset_type_name}')"
                        )
                except Exception as e:
                    logger.error(f"[Sensor] Error identifying candidate '{uri}' in source '{source.name}': {e}")

    def run_forever(self, interval: float = 3.0):
        """Continuously polls all registered AssetSources."""
        logger.info(f"[Sensor] Monitoring AssetSources (interval={interval}s)...")
        try:
            while True:
                self.run_once()
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("[Sensor] Watcher loop stopped by user.")
