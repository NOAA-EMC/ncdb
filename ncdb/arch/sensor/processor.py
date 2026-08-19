from __future__ import annotations

import importlib
import logging
import time
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from workflow import Workflow, AssetSource

logger = logging.getLogger(__name__)


def load_handler(handler_str: str) -> Any:
    if ":" not in handler_str:
        raise ValueError(
            f"Invalid handler string '{handler_str}'. "
            "Expected 'module:Class'"
        )

    module_path, class_name = handler_str.split(":", 1)
    module = importlib.import_module(module_path)

    return getattr(module, class_name)


class DataProcessor:
    """Discovers and identifies data products using configured detectors."""

    def __init__(self, workflow: Workflow, catalog):
        self.workflow = workflow
        self.catalog = catalog
        self._detector_cache: Dict[str, Any] = {}

    def _resolve_detector(self, source: AssetSource) -> Any:
        handler_str = source.handler

        if handler_str not in self._detector_cache:
            detector_cls = load_handler(handler_str)

            asset_types = self.workflow.list_asset_types()

            if isinstance(detector_cls, type):
                detector = detector_cls(asset_types)
            else:
                detector = detector_cls

            self._detector_cache[handler_str] = detector

        return self._detector_cache[handler_str]

    def run_once(self):
        sources = self.workflow.list_asset_sources()

        if not sources:
            logger.debug(
                "[DataProcessor] No AssetSources registered."
            )
            return

        for source in sources:

            try:
                detector = self._resolve_detector(source)
            except Exception as e:
                logger.error(
                    f"[DataProcessor] Failed to resolve handler "
                    f"'{source.handler}' for source "
                    f"'{source.name}': {e}"
                )
                continue

            try:
                candidate_uris = detector.discover(source)
            except Exception as e:
                logger.error(
                    f"[DataProcessor] Discovery failed for source "
                    f"'{source.name}': {e}"
                )
                continue

            for uri in candidate_uris:

                try:
                    result = detector.identify(
                        uri,
                        source,
                    )

                    if result is None:
                        continue

                    asset, context = result

                    self.catalog.register(
                        asset,
                        context,
                    )

                    logger.info(
                        f"[DataProcessor] [{source.name}] "
                        f"Discovered '{asset.uri}'"
                    )

                except Exception as e:
                    logger.error(
                        f"[DataProcessor] Error identifying candidate "
                        f"'{uri}' in source '{source.name}': {e}"
                    )

    def run_forever(self, interval: float = 3.0):
        logger.info(
            f"[DataProcessor] Monitoring AssetSources "
            f"(interval={interval}s)..."
        )

        try:
            while True:
                self.run_once()
                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info(
                "[DataProcessor] Watcher loop stopped by user."
            )
