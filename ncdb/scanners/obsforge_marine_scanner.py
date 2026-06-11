import logging
logger = logging.getLogger(__name__)

import os
from datetime import datetime

from .base import BaseScanner
from ncdb.ds.file import File
from ncdb.ds.dataset import Dataset


class ObsForgeMarineScanner(BaseScanner):

    def _parse_dataset_and_date(self, entry):
        """
        Parses top-level directory names like 'gdas.20260610'.
        Returns (model_name, cycle_date) or (None, None) if invalid.
        """
        if "." not in entry:
            return None, None
            
        model, date_str = entry.split(".", 1)
        if model == "logs" or not date_str.isdigit():
            return None, None
            
        try:
            cycle_date = datetime.strptime(date_str, "%Y%m%d").date()
            return model, cycle_date
        except ValueError:
            return None, None

    def parse_obs_space(self, file_path):
        """
        Extracts obs_space from filenames like:
        gdas.t06z.rads_adt_3a.nc -> rads_adt_3a
        """
        filename = os.path.basename(file_path)
        parts = filename.split(".")

        if len(parts) < 4 or parts[-1] != "nc":
            return None

        return parts[2]

    def discover_datasets(self):
        """
        Finds all unique model names that contain an 'ocean' directory structure.
        Maps each model to a single self-contained dataset object.
        """
        dataset_names = set()

        for entry in os.listdir(self.root_dir):
            top_dir = os.path.join(self.root_dir, entry)
            if not os.path.isdir(top_dir):
                continue

            model, _ = self._parse_dataset_and_date(entry)
            if not model:
                continue

            # Verify that at least one cycle hour contains an 'ocean' folder
            for hour in ["00", "06", "12", "18"]:
                ocean_dir = os.path.join(top_dir, hour, "ocean")
                if os.path.isdir(ocean_dir):
                    dataset_names.add(model)
                    break

        self.datasets = [
            Dataset(name=m, root_dir=self.root_dir)
            for m in sorted(dataset_names)
        ]

        return self.datasets

    def discover_cycles(self, dataset):
        """
        Finds valid dates and cycle hours where the 'ocean' folder exists for this model.
        """
        cycles = set()
        model = dataset.name

        for entry in os.listdir(self.root_dir):
            top_dir = os.path.join(self.root_dir, entry)
            if not os.path.isdir(top_dir):
                continue

            entry_model, cycle_date = self._parse_dataset_and_date(entry)
            if entry_model != model:
                continue

            for hour in ["00", "06", "12", "18"]:
                ocean_dir = os.path.join(top_dir, hour, "ocean")
                if os.path.isdir(ocean_dir):
                    # Confirm there are nested files or directories inside
                    if os.listdir(ocean_dir):
                        cycles.add((cycle_date, hour))

        return sorted(cycles)

    def scan_cycle(self, dataset, cycle_date, cycle_hour):
        """
        Scans all files recursively underneath the 'ocean' directory level.
        All sub-categories are loaded into this singular model dataset.
        """
        logger.info(f"Scanning marine dataset {dataset.name} cycle {cycle_date}, {cycle_hour}")
        
        model = dataset.name
        ocean_dir = os.path.join(
            self.root_dir,
            f"{model}.{cycle_date.strftime('%Y%m%d')}",
            cycle_hour,
            "ocean"
        )

        results = []
        if not os.path.isdir(ocean_dir):
            return results

        # Recursively walk through adt/, icec/, insitu/, sss/, sst/
        for dirpath, _, filenames in os.walk(ocean_dir):
            for f in filenames:
                if not f.endswith(".nc"):
                    continue

                full = os.path.join(dirpath, f)
                
                # Defensive check for broken symlinks
                if not os.path.isfile(full):
                    continue

                file_obj = File.from_path(full)
                obs_space = self.parse_obs_space(full)
                
                if obs_space:
                    results.append((file_obj, obs_space))

        return results
