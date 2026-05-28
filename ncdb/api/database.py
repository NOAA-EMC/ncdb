import logging
from typing import List, Optional
import os
from datetime import datetime, time

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from ncdb.ds.db_base import Base

from ncdb.ds.io.dataset_repository import DatasetRepository
from ncdb.scanners.marine_da_scanner import MarineDAScanner as DefaultScanner
from .dataset import Dataset

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path):
        self._db_path = db_path

        # clean fail if db dir is incorrect
        db_dir = os.path.dirname(os.path.abspath(self._db_path)) or "."
        if not os.path.exists(db_dir):
            raise ValueError(f"Database directory does not exist: {db_dir}")
        if not os.path.isdir(db_dir):
            raise ValueError(f"Database path is not a directory: {db_dir}")
        if not os.access(db_dir, os.W_OK):
            raise PermissionError(f"Database directory is not writable: {db_dir}")

        self._engine = create_engine(f"sqlite:///{self._db_path}")
        self._session = Session(self._engine)

        Base.metadata.create_all(self._engine)

        self._repo = DatasetRepository(self._session)

    @property
    def path(self):
        return self._db_path

    def scan(
        self,
        data_root: str,
        n_cycles: Optional[int],
        scanner_cls=DefaultScanner,
        callback=None
    ):

        started_at = datetime.utcnow()

        report = {
            "status": "running",
            "started_at": started_at.isoformat(),

            "data_root": data_root,
            "scanner": scanner_cls.__name__,
            "n_cycles": n_cycles,

            "datasets_discovered": 0,
            "cycles_scanned": 0,

            "datasets": [],
            "cycles": [],

            "warnings": [],
            "errors": [],
        }

        try:
            message = f"Scanning data root: {data_root}"
            if callback:
                callback(message)
            logger.info(message)

            # discover datasets
            scanner = scanner_cls(data_root)

            for ds in scanner.datasets:
                # print(f"scanner dataset {ds}")
                try:
                    self._repo.save_dataset(ds)
                    # update in memory state of the dataset
                    self._repo.load_fields(ds)
                    print(f"    LOADED  dataset {ds}")

                    report["datasets"].append({
                        "name": ds.name,
                        "root_dir": ds.root_dir,
                    })
                    report["datasets_discovered"] += 1

                except Exception as e:
                    logger.exception(
                        f"Failed to save dataset {ds.name}"
                    )
                    report["errors"].append({
                        "stage": "dataset_discovery",
                        "dataset": ds.name,
                        "error": str(e),
                    })

            #
            # scan cycles
            #
            for cycle in scanner.scan_dataset_cycles(n_cycles):
                cycle_hour = int(cycle.cycle_hour)

                cycle_id = (
                    f"{cycle.cycle_date} "
                    f"{cycle_hour:02d}"
                )

                try:
                    if callback:
                        callback(f"Scanning cycle {cycle_id}")
                    logger.info(
                        f"Scanning cycle {cycle_id}"
                    )

                    ds_cycle = cycle.dataset.build_cycle(
                        cycle.cycle_date,
                        cycle.cycle_hour,
                        cycle.scan_results
                    )

                    self._repo.save_scan(ds_cycle)

                    report["cycles"].append({
                        "dataset": cycle.dataset.name,
                        "cycle_date": str(cycle.cycle_date),
                        # "cycle_hour": int(cycle.cycle_hour),
                        "cycle_hour": cycle_hour,
                        "n_files": len(ds_cycle.files),
                    })
                    report["cycles_scanned"] += 1

                except Exception as e:
                    logger.exception(
                        f"Failed cycle {cycle_id}"
                    )
                    report["errors"].append({
                        "stage": "cycle_scan",
                        "dataset": cycle.dataset.name,
                        "cycle_date": str(cycle.cycle_date),
                        "cycle_hour": int(cycle.cycle_hour),
                        "error": str(e),
                    })

            self._session.commit()

            report["status"] = "success"

        except Exception as e:
            logger.exception("Fatal scan failure")
            report["status"] = "failed"
            report["errors"].append({
                "stage": "fatal",
                "error": str(e),
            })
            self._session.rollback()

        finished_at = datetime.utcnow()
        report["finished_at"] = (
            finished_at.isoformat()
        )
        report["duration_seconds"] = (
            finished_at - started_at
        ).total_seconds()
        logger.info("Scan complete")

        return report

    def datasets(
        self,
        name: str | None = None,
        root_dir: str | None = None,
    ) -> list[Dataset]:

        datasets = self._repo.get_all_datasets()

        if name is not None:
            datasets = [
                d for d in datasets
                if d.name == name
            ]

        if root_dir is not None:
            datasets = [
                d for d in datasets
                if d.root_dir == root_dir
            ]

        return [
            Dataset(d, self._repo)
            for d in datasets
        ]

    # def datasets(self) -> list[Dataset]:
        # return [
            # Dataset(d, self._repo)
            # for d in self._repo.get_all_datasets()
        # ]


    def dataset(self, key, root_dir=None):

        datasets = self._repo.get_all_datasets()

        #
        # lookup by integer id
        #
        if isinstance(key, int):
            for d in datasets:
                if d.id == key:
                    return Dataset(d, self._repo)
            raise ValueError(
                f"Dataset id '{key}' not found"
            )

        #
        # lookup by name
        #
        if isinstance(key, str):
            matches = [
                d for d in datasets
                if d.name == key
            ]
            #
            # optional root_dir disambiguation
            #
            if root_dir is not None:
                matches = [
                    d for d in matches
                    if d.root_dir == root_dir
                ]
            if len(matches) == 0:
                raise ValueError(
                    f"Dataset not found "
                    f"name={key} root_dir={root_dir}"
                )

            if len(matches) > 1:
                raise ValueError(
                    f"Multiple datasets found "
                    f"name={key}; specify root_dir"
                )

            return Dataset(matches[0], self._repo)

        raise TypeError(
            f"Unsupported dataset key type: {type(key)}"
        )


    def try_dataset(
        self,
        name: str | None = None,
        root_dir: str | None = None,
        id: int | None = None,
    ):
        """
        Load a dataset.

        Parameters
        ----------
        id : int
            Dataset database id.

        name : str
            Dataset name.

        root_dir : str
            Dataset root directory.
        """

        datasets = self._repo.get_all_datasets()

        #
        # lookup by id
        #
        if id is not None:
            matches = [
                d for d in datasets
                if d.id == id
            ]
            if not matches:
                raise ValueError(
                    f"Dataset id '{id}' not found"
                )
            return Dataset(matches[0], self._repo)

        #
        # lookup by name/root_dir
        #
        if name is not None:
            matches = [
                d for d in datasets
                if d.name == name
            ]
            if root_dir is not None:
                matches = [
                    d for d in matches
                    if d.root_dir == root_dir
                ]
            if len(matches) == 0:
                raise ValueError(
                    f"Dataset not found "
                    f"name={name} "
                    f"root_dir={root_dir}"
                )
            if len(matches) > 1:
                raise ValueError(
                    f"Multiple datasets found "
                    f"name={name} "
                    f"root_dir={root_dir}"
                )

            return Dataset(matches[0], self._repo)

        raise ValueError(
            "dataset() requires either "
            "id or name"
        )

##################

    def old_dataset(self, key):
        """
        Load dataset by id or name.

        Parameters
        ----------
        key : int | str
            Dataset id or dataset name.
        """

        datasets = self._repo.get_all_datasets()

        #
        # lookup by integer id
        #
        if isinstance(key, int):
            for d in datasets:
                if d.id == key:
                    return Dataset(d, self._repo)

            raise ValueError(f"Dataset id '{key}' not found")

        #
        # lookup by name
        #
        if isinstance(key, str):
            matches = [
                d for d in datasets
                if d.name == key
            ]

            if len(matches) == 0:
                raise ValueError(f"Dataset '{key}' not found")

            #
            # temporary behavior:
            # return first match
            #
            if len(matches) > 1:
                logger.warning(
                    f"Multiple datasets named '{key}' found; "
                    f"returning first match"
                )

            return Dataset(matches[0], self._repo)

        raise TypeError(
            f"Unsupported dataset key type: {type(key)}"
        )

    def old_cycles(self, dataset_name: Optional[str] = None):
        if dataset_name:
            ds = self.dataset(dataset_name)
            self._repo.load_cycles(ds)
            datasets = [ds]
        else:
            datasets = self._repo.get_all_datasets()
            for ds in datasets:
                self._repo.load_cycles(ds)

        seen = set()
        result = []

        for ds in datasets:
            for c in ds.cycles:
                key = (c.cycle_date, c.cycle_hour)
                if key in seen:
                    continue
                seen.add(key)
                result.append(c)

        # sort globally
        result.sort(key=lambda c: (c.cycle_date, c.cycle_hour))

        return [
            datetime(
                c.cycle_date.year,
                c.cycle_date.month,
                c.cycle_date.day,
                int(c.cycle_hour),
            )
            for c in result
        ]
