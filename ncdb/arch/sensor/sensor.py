from __future__ import annotations

import importlib
import json
import logging
import os
import time
from typing import TYPE_CHECKING, Any, Dict, List

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .orm import Base, AssetSourceORM
from .asset_source import AssetSource

if TYPE_CHECKING:
    from workflow import Workflow

logger = logging.getLogger(__name__)


def load_handler(handler_str: str) -> Any:
    if ":" not in handler_str:
        raise ValueError(f"Invalid handler string '{handler_str}'. Expected 'module:Class'")
    module_path, class_name = handler_str.split(":", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


class Sensor:
    """Discovers and identifies assets using configured detectors."""

    def __init__(
        self,
        workflow: Workflow,
        catalog: Any,
        db_path: str = "obsforge-sensor.db",
    ):
        self.workflow = workflow
        self.catalog = catalog
        self._detector_cache: Dict[str, Any] = {}

        # Sensor DB management for AssetSources
        self._db_path = os.path.abspath(db_path)
        self._engine = create_engine(f"sqlite:///{self._db_path}")
        self._session_factory = sessionmaker(bind=self._engine)
        Base.metadata.create_all(self._engine)

    def _get_session(self):
        return self._session_factory()

    def register_asset_source(self, source: AssetSource) -> AssetSource:
        """Registers an AssetSource domain object in the sensor database."""
        with self._get_session() as session:
            existing = session.query(AssetSourceORM).filter_by(name=source.name).first()
            if existing:
                logger.info(f"[Sensor] AssetSource '{source.name}' already exists (id={existing.id}).")
                return AssetSource.from_orm(existing)

            param_str = json.dumps(source.parameters) if source.parameters else None
            source_orm = AssetSourceORM(
                name=source.name,
                handler=source.handler,
                parameters=param_str,
            )
            session.add(source_orm)
            session.commit()
            session.refresh(source_orm)
            logger.info(f"[Sensor] Registered new AssetSource '{source.name}' (id={source_orm.id}).")
            return AssetSource.from_orm(source_orm)

    def list_asset_sources(self) -> List[AssetSource]:
        """Lists all registered AssetSources from the sensor database."""
        with self._get_session() as session:
            sources_orm = session.query(AssetSourceORM).all()
            return [AssetSource.from_orm(s) for s in sources_orm]

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
        sources = self.list_asset_sources()
        if not sources:
            logger.debug("[Sensor] No AssetSources registered in sensor DB.")
            return

        known_uris = {asset.uri for asset in self.workflow.list_assets()}

        for source in sources:
            try:
                detector = self._resolve_detector(source)
            except Exception as e:
                logger.error(f"[Sensor] Failed to resolve handler '{source.handler}': {e}")
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
                    result = detector.identify(uri, source)
                    if result is None:
                        continue

                    asset, context = result
                    registered_asset = self.workflow.register_asset(asset)
                    known_uris.add(uri)

                    self.catalog.register(registered_asset, context)
                    logger.info(
                        f"[Sensor] Registered '{registered_asset.uri}' as Asset #{registered_asset.id}"
                    )

                except Exception as e:
                    logger.error(f"[Sensor] Error identifying candidate '{uri}': {e}")

    def run_forever(self, interval: float = 3.0):
        logger.info(f"[Sensor] Monitoring AssetSources (interval={interval}s)...")
        try:
            while True:
                self.run_once()
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("[Sensor] Watcher loop stopped by user.")
