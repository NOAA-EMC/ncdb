import logging
logger = logging.getLogger(__name__)

from typing import List, Optional
from datetime import datetime
import pandas as pd

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from .dataset_orm import (
    FieldORM
    # CycleORM,
    # DatasetFileORM
)

from .dataset_file import DatasetFile


class Field:
    """
    Represents a variable of type ObsSpace within a Dataset.
    It has a list of DatasetFile objects (0 or 1 per cycle)
    A DatasetFile object is a link between field, cycle and file
    """
    def __init__(self, dataset: "Dataset", obs_space: "ObsSpace"):
        self.dataset = dataset
        self.obs_space = obs_space
        self.id = None  # set when persisted

        # the files are not persisted here, but in cycles
        self.files: List[DatasetFile] = []

    def __repr__(self) -> str:
        return (
            f"<Field id = {self.id}: "
            f"{self.dataset.name} "
            f"{self.obs_space},\n"
            f"{len(self.files)} files>"
        )

    def add_file(self, f: DatasetFile):
        self.files.append(f)

    @classmethod
    def from_orm(cls, orm: FieldORM, dataset: "Dataset") -> "Field":
        if not orm:
            return None

        from .obs_space import ObsSpace
        obs_space_domain = ObsSpace.from_orm(orm.obs_space)

        instance = cls(dataset=dataset, obs_space=obs_space_domain)
        instance.id = orm.id
        # logger.info(f"Field.from_orm = {instance}")
        return instance

    def to_orm(self) -> FieldORM:
        return FieldORM(
            id=self.id,
            dataset_id=self.dataset.id,
            obs_space_id=self.obs_space.id
        )

    # def find_file_for_time(self, time: datetime) -> Optional[DatasetFile]:
        # for f in self.files:
            # if f.dataset_cycle.datetime == time:
                # return f
        # return None


    def find_file_for_time(self, date, hour: int):
        """
        Finds the DatasetFile corresponding to a given cycle.

        Assumes:
        - At most one file per cycle
        - self.files already loaded
        """
        hour_str = f"{hour:02d}"

        for f in self.files:
            c = f.dataset_cycle

            if c.cycle_date == date and c.cycle_hour == hour_str:
                return f

        return None

    # checking derived attribute:
    # very inefficient.... to be improved
    def has_derived(self, variable_path: str, name: str) -> bool:
        for f in self.files:
            if f.has_derived(variable_path, name):
                return True
        return False

    # the derived attributes of a field are the same for all files
    def list_derived_attributes(self, variable_path: str):
        if self.files:
            f = self.files[0]
            if f:
                nc_file = f.netcdf_file
                if nc_file:
                    return nc_file.list_derived(variable_path)
        return []
