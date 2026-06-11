import logging
logger = logging.getLogger(__name__)

import os
from datetime import datetime

from .base import BaseScanner
from ncdb.ds.file import File
from ncdb.ds.dataset import Dataset


class ObsForgeScanner(BaseScanner):

    def _parse_dataset_and_date(self, entry):
        """
        Parses top-level directory names like 'gdas.20260603'.
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
        gdas.t12z.radiance_amsua_metop-b.nc -> radiance_amsua_metop-b
        """
        filename = os.path.basename(file_path)
        parts = filename.split(".")

        # Pattern: <model>.<tHHz>.<obs_space>.nc
        if len(parts) < 4 or parts[-1] != "nc":
            return None

        # Join everything between the cycle string (parts[1]) and '.nc'
        # just in case obs_space contains extra dots in the future
        return parts[2]

    def discover_datasets(self):
        """
        Discovers all sub-directory datasets across the layout.
        Maps any directory containing .nc files into a unique string identifier.
        """
        dataset_names = set()

        for entry in os.listdir(self.root_dir):
            top_dir = os.path.join(self.root_dir, entry)
            if not os.path.isdir(top_dir):
                continue

            model, _ = self._parse_dataset_and_date(entry)
            if not model:
                continue

            # Deep-crawl to find leaf directories containing netCDF files
            for dirpath, _, filenames in os.walk(top_dir):
                if any(f.endswith(".nc") for f in filenames):
                    # Get the path relative to the top date directory (e.g., '12/atmos' or '12/ocean/insitu')
                    rel_sub_path = os.path.relpath(dirpath, top_dir)
                    path_parts = rel_sub_path.split(os.sep)
                    
                    if len(path_parts) > 1:
                        # Skip the hour component (path_parts[0]) to get the structural path components
                        sub_dir_suffix = "_".join(path_parts[1:])
                        ds_name = f"{model}_{sub_dir_suffix}"
                        dataset_names.add(ds_name)

        self.datasets = [
            Dataset(name=d, root_dir=self.root_dir)
            for d in sorted(dataset_names)
        ]
        logger.info(f"Discovered datasets {dataset_names}")

        return self.datasets

    def discover_cycles(self, dataset):
        """
        Finds valid dates and cycle hours where this specific dataset signature exists.
        """
        cycles = set()
        # Reconstruct the original model name and directory suffix from the dataset name
        # e.g., 'gfs_ocean_insitu' -> model='gfs', suffix_parts=['ocean', 'insitu']
        parts = dataset.name.split("_")
        model = parts[0]
        suffix_parts = parts[1:]

        for entry in os.listdir(self.root_dir):
            top_dir = os.path.join(self.root_dir, entry)
            if not os.path.isdir(top_dir):
                continue

            entry_model, cycle_date = self._parse_dataset_and_date(entry)
            if entry_model != model:
                continue

            # Check potential cycle hours (00, 06, 12, 18)
            for hour in ["00", "06", "12", "18"]:
                target_dir = os.path.join(top_dir, hour, *suffix_parts)
                
                # Verify this specific dataset component exists for this cycle hour
                if os.path.isdir(target_dir):
                    if any(f.endswith(".nc") for f in os.listdir(target_dir)):
                        cycles.add((cycle_date, hour))

        return sorted(cycles)

    def scan_cycle(self, dataset, cycle_date, cycle_hour):
        """
        Scans a specific leaf directory for a target dataset/cycle pairing.
        """
        logger.info(f"Scanning {dataset.name} cycle {cycle_date}, {cycle_hour}")
        
        parts = dataset.name.split("_")
        model = parts[0]
        suffix_parts = parts[1:]

        # Construct the explicit path down to the target leaf folder
        ds_dir = os.path.join(
            self.root_dir,
            f"{model}.{cycle_date.strftime('%Y%m%d')}",
            cycle_hour,
            *suffix_parts
        )

        results = []
        if not os.path.isdir(ds_dir):
            return results

        # Read only the contents of this explicit directory level (no recursion into other datasets)
        for f in os.listdir(ds_dir):
            if not f.endswith(".nc"):
                continue

            full = os.path.join(ds_dir, f)
            
            # Defensive check if it's a broken symlink
            if not os.path.isfile(full):
                continue

            file_obj = File.from_path(full)
            obs_space = self.parse_obs_space(full)
            
            if obs_space:
                results.append((file_obj, obs_space))

        return results
