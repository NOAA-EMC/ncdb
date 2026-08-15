from .base import Base

# Existing dataset model
from .dataset_orm import DatasetORM
from .cycle_orm import CycleORM
from .field_orm import FieldORM
from .dataset_file_orm import DatasetFileORM

# Existing observation-space model
from .obs_space_orm import ObsSpaceORM

# New logical observation model
from .variable_orm import (
    VariableORM,
    ObsSpaceVariableORM,
    # DataProductORM,
    # DataProductVariableORM,
)

# NetCDF physical representation
from .netcdf_structure_orm import (
    NetcdfNodeORM,
    NetcdfStructureORM,
    NetcdfStructureAttributeORM,
    NetcdfVariableDimensionORM,
)

from .netcdf_file_orm import (
    NetcdfFileAttributeORM,
    NetcdfFileDerivedAttributeORM,
)

# Physical storage
from .file_orm import FileORM
from .storage_orm import StorageORM


__all__ = [
    "Base",

    # Existing compatibility model
    "DatasetORM",
    "CycleORM",
    "FieldORM",
    "DatasetFileORM",

    # Logical observation model
    "ObsSpaceORM",
    "VariableORM",
    "ObsSpaceVariableORM",
    # "DataProductORM",
    # "DataProductVariableORM",

    # NetCDF representation
    "NetcdfNodeORM",
    "NetcdfStructureORM",
    "NetcdfStructureAttributeORM",
    "NetcdfVariableDimensionORM",
    "NetcdfFileAttributeORM",
    "NetcdfFileDerivedAttributeORM",

    # Physical storage
    "FileORM",
    "StorageORM",
]
