from __future__ import annotations

import logging
import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker, joinedload

from workflow_orm import (
    Base, 
    AssetTypeORM, 
    AssetORM, 
    TransformationORM, 
    TransformationInputORM, 
    TransformationOutputORM,
    JobORM, 
    JobInputAssetORM, 
    JobOutputAssetORM
)

from transformation import Transformation
from job import Job
from asset import Asset
from asset_type import AssetType

logger = logging.getLogger(__name__)


class Workflow:
    def __init__(self, db_path: str):
        self._db_path = os.path.abspath(db_path)
        db_dir = os.path.dirname(self._db_path)

        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
        if not os.access(db_dir, os.W_OK):
            raise PermissionError(f"Database directory is not writable: {db_dir}")

        self._engine = create_engine(
            f"sqlite:///{self._db_path}",
            connect_args={
                "check_same_thread": False,
                "timeout": 30.0  # Wait up to 30s during concurrent process writes
            }
        )

        # Enable SQLite Write-Ahead Logging (WAL) and synchronous settings for concurrent processes
        @event.listens_for(self._engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.close()

        self._session_factory = sessionmaker(bind=self._engine)

        Base.metadata.create_all(self._engine)

    def _get_session(self) -> Session:
        return self._session_factory()

    def register_asset_type(self, name: str, description: Optional[str] = None) -> AssetType:
        """Registers a new AssetType in the database and returns a domain AssetType object."""
        with self._get_session() as session:
            existing = session.query(AssetTypeORM).filter_by(name=name).first()
            if existing:
                logger.info(f"AssetType '{name}' already exists (id={existing.id}).")
                return AssetType.from_orm(existing)

            asset_type_orm = AssetTypeORM(name=name, description=description)
            session.add(asset_type_orm)
            session.commit()
            session.refresh(asset_type_orm)
            logger.info(f"Registered new AssetType '{name}' (id={asset_type_orm.id}).")
            return AssetType.from_orm(asset_type_orm)

    def list_asset_types(self) -> List[AssetType]:
        """Lists all registered AssetTypes as domain objects."""
        with self._get_session() as session:
            return [AssetType.from_orm(at) for at in session.query(AssetTypeORM).all()]

    def register_asset(
        self, 
        uri: str, 
        asset_type: AssetType, 
        state: str = "AVAILABLE", 
        fingerprint: Optional[str] = None
    ) -> Asset:
        """Registers a new physical Asset linked to an AssetType domain object."""
        with self._get_session() as session:
            existing = session.query(AssetORM).options(joinedload(AssetORM.asset_type)).filter_by(uri=uri).first()
            if existing:
                logger.info(f"Asset '{uri}' already registered (id={existing.id}).")
                return Asset.from_orm(existing)

            asset_orm = AssetORM(
                asset_type_id=asset_type.id,
                uri=uri,
                state=state,
                fingerprint=fingerprint,
            )
            session.add(asset_orm)
            session.commit()
            
            reloaded = session.query(AssetORM).options(joinedload(AssetORM.asset_type)).get(asset_orm.id)
            logger.info(f"Registered new Asset '{uri}' (id={reloaded.id}).")
            return Asset.from_orm(reloaded)

    def list_assets(
        self, 
        asset_type: Optional[AssetType] = None, 
        state: Optional[str] = None
    ) -> List[Asset]:
        """Lists registered Assets, optionally filtered by domain AssetType or state."""
        with self._get_session() as session:
            query = session.query(AssetORM).options(joinedload(AssetORM.asset_type))

            if asset_type:
                query = query.filter(AssetORM.asset_type_id == asset_type.id)

            if state:
                query = query.filter(AssetORM.state == state)

            return [Asset.from_orm(a) for a in query.all()]

    def register_transformation(
        self,
        name: str,
        handler: str,
        input_asset_types: List[AssetType],
        output_asset_types: List[AssetType],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Transformation:
        """Register a transformation blueprint linking input AssetTypes to output AssetTypes."""
        with self._get_session() as session:
            # Check if transformation already exists
            existing = (
                session.query(TransformationORM)
                .options(
                    joinedload(TransformationORM.inputs).joinedload(TransformationInputORM.asset_type),
                    joinedload(TransformationORM.outputs).joinedload(TransformationOutputORM.asset_type),
                )
                .filter_by(name=name)
                .first()
            )
            if existing:
                logger.info(f"Transformation '{name}' already exists (id={existing.id}).")
                return Transformation.from_orm(existing)

            # 1. Create main Transformation record
            param_str = json.dumps(parameters) if parameters else None
            trans_orm = TransformationORM(
                name=name,
                handler=handler,
                parameters=param_str,
            )
            session.add(trans_orm)
            session.flush()

            # 2. Map input asset types directly by ID
            for at in input_asset_types:
                session.add(
                    TransformationInputORM(
                        transformation_id=trans_orm.id,
                        asset_type_id=at.id,
                    )
                )

            # 3. Map output asset types directly by ID
            for at in output_asset_types:
                session.add(
                    TransformationOutputORM(
                        transformation_id=trans_orm.id,
                        asset_type_id=at.id,
                    )
                )

            session.commit()

            reloaded = (
                session.query(TransformationORM)
                .options(
                    joinedload(TransformationORM.inputs).joinedload(TransformationInputORM.asset_type),
                    joinedload(TransformationORM.outputs).joinedload(TransformationOutputORM.asset_type),
                )
                .get(trans_orm.id)
            )

            logger.info(f"Registered new Transformation '{name}' (id={reloaded.id}).")
            return Transformation.from_orm(reloaded)

    def list_transformations(self) -> List[Transformation]:
        """List all registered transformations as domain objects."""
        with self._get_session() as session:
            transformations_orm = (
                session.query(TransformationORM)
                .options(
                    joinedload(TransformationORM.inputs).joinedload(TransformationInputORM.asset_type),
                    joinedload(TransformationORM.outputs).joinedload(TransformationOutputORM.asset_type),
                )
                .all()
            )
            return [Transformation.from_orm(t) for t in transformations_orm]

    def create_job(self, transformation: Transformation, input_assets: List[Asset]) -> Job:
        """Creates a PENDING job given a Transformation domain object and input Asset domain objects."""
        with self._get_session() as session:
            trans_orm = session.query(TransformationORM).get(transformation.id)
            if not trans_orm:
                raise ValueError(f"Transformation id={transformation.id} ('{transformation.name}') not found in DB.")

            job_orm = JobORM(transformation_id=trans_orm.id, state="PENDING")
            session.add(job_orm)
            session.flush()

            # Attach input assets by primary key ID
            for asset in input_assets:
                asset_orm = session.query(AssetORM).get(asset.id)
                if not asset_orm:
                    raise ValueError(f"Asset id={asset.id} ('{asset.uri}') not found in DB.")
                jia = JobInputAssetORM(job_id=job_orm.id, asset_id=asset_orm.id)
                session.add(jia)

            session.commit()

            reloaded = (
                session.query(JobORM)
                .options(
                    joinedload(JobORM.transformation).joinedload(TransformationORM.inputs).joinedload(TransformationInputORM.asset_type),
                    joinedload(JobORM.transformation).joinedload(TransformationORM.outputs).joinedload(TransformationOutputORM.asset_type),
                    joinedload(JobORM.job_input_assets).joinedload(JobInputAssetORM.asset).joinedload(AssetORM.asset_type),
                    joinedload(JobORM.job_output_assets).joinedload(JobOutputAssetORM.asset).joinedload(AssetORM.asset_type),
                )
                .get(job_orm.id)
            )
            return Job.from_orm(reloaded)

    def claim_job(self) -> Optional[Job]:
        """Fetches the oldest PENDING job."""
        with self._get_session() as session:
            job_orm = (
                session.query(JobORM)
                .options(
                    joinedload(JobORM.transformation).joinedload(TransformationORM.inputs).joinedload(TransformationInputORM.asset_type),
                    joinedload(JobORM.transformation).joinedload(TransformationORM.outputs).joinedload(TransformationOutputORM.asset_type),
                    joinedload(JobORM.job_input_assets).joinedload(JobInputAssetORM.asset).joinedload(AssetORM.asset_type),
                    joinedload(JobORM.job_output_assets).joinedload(JobOutputAssetORM.asset).joinedload(AssetORM.asset_type),
                )
                .filter_by(state="PENDING")
                .order_by(JobORM.created_at.asc())
                .first()
            )
            if job_orm:
                return Job.from_orm(job_orm)
            return None

    def mark_job_success(
        self, 
        job_id: int, 
        output_uris: List[str], 
        output_asset_type: AssetType
    ) -> Job:
        """Marks a job as SUCCESS, registers generated output assets, links them by ID, and returns the updated Job."""
        with self._get_session() as session:
            job_orm = session.query(JobORM).get(job_id)
            if not job_orm:
                raise ValueError(f"Job id={job_id} not found.")

            job_orm.state = "SUCCESS"
            job_orm.finished_at = datetime.utcnow()

            # Register generated output assets using AssetType ID directly
            for uri in output_uris:
                asset = session.query(AssetORM).filter_by(uri=uri).first()
                if not asset:
                    asset = AssetORM(uri=uri, asset_type_id=output_asset_type.id, state="AVAILABLE")
                    session.add(asset)
                    session.flush()

                joa = JobOutputAssetORM(job_id=job_orm.id, asset_id=asset.id)
                session.add(joa)

            session.commit()

            reloaded = (
                session.query(JobORM)
                .options(
                    joinedload(JobORM.transformation).joinedload(TransformationORM.inputs).joinedload(TransformationInputORM.asset_type),
                    joinedload(JobORM.transformation).joinedload(TransformationORM.outputs).joinedload(TransformationOutputORM.asset_type),
                    joinedload(JobORM.job_input_assets).joinedload(JobInputAssetORM.asset).joinedload(AssetORM.asset_type),
                    joinedload(JobORM.job_output_assets).joinedload(JobOutputAssetORM.asset).joinedload(AssetORM.asset_type),
                )
                .get(job_orm.id)
            )
            return Job.from_orm(reloaded)

    def mark_job_running(self, job_id: int) -> Job:
        """Marks a claimed job as RUNNING and returns the updated Job domain object."""
        with self._get_session() as session:
            job_orm = session.query(JobORM).get(job_id)
            if not job_orm:
                raise ValueError(f"Job id={job_id} not found.")

            job_orm.state = "RUNNING"
            job_orm.started_at = datetime.utcnow()
            session.commit()

            reloaded = (
                session.query(JobORM)
                .options(
                    joinedload(JobORM.transformation).joinedload(TransformationORM.inputs).joinedload(TransformationInputORM.asset_type),
                    joinedload(JobORM.transformation).joinedload(TransformationORM.outputs).joinedload(TransformationOutputORM.asset_type),
                    joinedload(JobORM.job_input_assets).joinedload(JobInputAssetORM.asset).joinedload(AssetORM.asset_type),
                    joinedload(JobORM.job_output_assets).joinedload(JobOutputAssetORM.asset).joinedload(AssetORM.asset_type),
                )
                .get(job_id)
            )
            return Job.from_orm(reloaded)

    def mark_job_failed(self, job_id: int, error_log: str) -> Job:
        """Marks a job as FAILED with error details and returns the updated Job domain object."""
        with self._get_session() as session:
            job_orm = session.query(JobORM).get(job_id)
            if not job_orm:
                raise ValueError(f"Job id={job_id} not found.")

            job_orm.state = "FAILED"
            job_orm.finished_at = datetime.utcnow()
            job_orm.error_log = error_log
            session.commit()

            reloaded = (
                session.query(JobORM)
                .options(
                    joinedload(JobORM.transformation).joinedload(TransformationORM.inputs).joinedload(TransformationInputORM.asset_type),
                    joinedload(JobORM.transformation).joinedload(TransformationORM.outputs).joinedload(TransformationOutputORM.asset_type),
                    joinedload(JobORM.job_input_assets).joinedload(JobInputAssetORM.asset).joinedload(AssetORM.asset_type),
                    joinedload(JobORM.job_output_assets).joinedload(JobOutputAssetORM.asset).joinedload(AssetORM.asset_type),
                )
                .get(job_id)
            )
            return Job.from_orm(reloaded)

    def list_jobs(self, state: Optional[str] = None) -> List[Job]:
        """Returns a list of all jobs in the workflow system as domain objects."""
        with self._get_session() as session:
            query = (
                session.query(JobORM)
                .options(
                    joinedload(JobORM.transformation).joinedload(TransformationORM.inputs).joinedload(TransformationInputORM.asset_type),
                    joinedload(JobORM.transformation).joinedload(TransformationORM.outputs).joinedload(TransformationOutputORM.asset_type),
                    joinedload(JobORM.job_input_assets).joinedload(JobInputAssetORM.asset).joinedload(AssetORM.asset_type),
                    joinedload(JobORM.job_output_assets).joinedload(JobOutputAssetORM.asset).joinedload(AssetORM.asset_type),
                )
            )
            
            if state:
                query = query.filter(JobORM.state == state)

            jobs_orm = query.all()
            return [Job.from_orm(j) for j in jobs_orm]
