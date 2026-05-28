import logging
logger = logging.getLogger(__name__)

import os
from datetime import datetime

from .base import BaseScanner
from ncdb.ds.file import File
from ncdb.ds.dataset import Dataset


class ObsForgeScanner(BaseScanner):

    VALID_HOURS = {"00", "06", "12", "18"}

    def parse_obs_space(self, file_path):

        filename = os.path.basename(file_path)

        parts = filename.split(".")

        if len(parts) < 4:

            logger.debug(
                f"Invalid ObsForge filename: "
                f"{filename}"
            )

            return None

        if parts[-1] != "nc":
            return None

        return parts[2]

    def discover_datasets(self):

        if not os.path.isdir(self.root_dir):

            logger.error(
                f"Invalid root directory: "
                f"{self.root_dir}"
            )

            return []

        try:

            entries = os.listdir(self.root_dir)

        except Exception:

            logger.exception(
                f"Failed listing root directory "
                f"{self.root_dir}"
            )

            return []

        dataset_names = set()

        for entry in entries:

            full = os.path.join(
                self.root_dir,
                entry
            )

            try:

                if not os.path.isdir(full):
                    continue

            except Exception:

                logger.exception(
                    f"Failed checking directory "
                    f"{full}"
                )

                continue

            if "." not in entry:
                continue

            try:

                name, date_str = entry.split(".", 1)

            except ValueError:

                logger.warning(
                    f"Unexpected directory format: "
                    f"{entry}"
                )

                continue

            if not date_str.isdigit():
                continue

            dataset_names.add(name)

        datasets = [
            Dataset(
                name=name,
                root_dir=self.root_dir
            )
            for name in sorted(dataset_names)
        ]

        logger.info(
            f"Discovered "
            f"{len(datasets)} datasets: "
            f"{[d.name for d in datasets]}"
        )

        return datasets

    def discover_cycles(self, dataset):

        cycles = set()

        try:

            entries = os.listdir(self.root_dir)

        except Exception:

            logger.exception(
                f"Failed listing root directory "
                f"{self.root_dir}"
            )

            return []

        for entry in entries:

            if not entry.startswith(
                dataset.name + "."
            ):
                continue

            try:

                name, date_str = entry.split(".", 1)

            except ValueError:

                logger.warning(
                    f"Invalid dataset directory: "
                    f"{entry}"
                )

                continue

            try:

                cycle_date = datetime.strptime(
                    date_str,
                    "%Y%m%d"
                ).date()

            except ValueError:

                logger.warning(
                    f"Invalid cycle date: "
                    f"{date_str}"
                )

                continue

            ds_dir = os.path.join(
                self.root_dir,
                entry
            )

            try:

                hour_entries = os.listdir(ds_dir)

            except Exception:

                logger.exception(
                    f"Failed listing dataset dir "
                    f"{ds_dir}"
                )

                continue

            for hour in hour_entries:

                if hour not in self.VALID_HOURS:
                    continue

                cycles.add(
                    (cycle_date, hour)
                )

        discovered = sorted(cycles)

        logger.info(
            f"Discovered "
            f"{len(discovered)} cycles "
            f"for dataset {dataset.name}"
        )

        return discovered

    def scan_cycle(
        self,
        dataset,
        cycle_date,
        cycle_hour
    ):

        logger.info(
            f"Scanning "
            f"{dataset.name} "
            f"{cycle_date} "
            f"{cycle_hour}"
        )

        ds_dir = os.path.join(
            self.root_dir,
            f"{dataset.name}."
            f"{cycle_date.strftime('%Y%m%d')}",
            cycle_hour
        )

        if not os.path.isdir(ds_dir):

            logger.warning(
                f"Missing cycle directory: "
                f"{ds_dir}"
            )

            return []

        results = []

        scanned_files = 0
        accepted_files = 0

        try:

            for dirpath, _, filenames in os.walk(ds_dir):

                for filename in filenames:

                    scanned_files += 1

                    if not filename.endswith(".nc"):
                        continue

                    full = os.path.join(
                        dirpath,
                        filename
                    )

                    try:

                        file_obj = File.from_path(
                            full
                        )

                    except Exception:

                        logger.exception(
                            f"Failed reading file "
                            f"{full}"
                        )

                        continue

                    try:

                        obs_space = (
                            self.parse_obs_space(
                                full
                            )
                        )

                    except Exception:

                        logger.exception(
                            f"Failed parsing "
                            f"ObsSpace from "
                            f"{full}"
                        )

                        continue

                    if not obs_space:

                        logger.debug(
                            f"Skipping file with "
                            f"unknown ObsSpace: "
                            f"{full}"
                        )

                        continue

                    results.append(
                        (file_obj, obs_space)
                    )

                    accepted_files += 1

        except Exception:

            logger.exception(
                f"Failed walking directory "
                f"{ds_dir}"
            )

        logger.info(
            f"Completed scan "
            f"{dataset.name} "
            f"{cycle_date} "
            f"{cycle_hour} "
            f"files={scanned_files} "
            f"accepted={accepted_files}"
        )

        return results
