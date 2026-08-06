import logging
logger = logging.getLogger(__name__)

from typing import Optional

from ncdb.orm import DatasetFileORM
from .netcdf_file import NetcdfFile
from .file import File


'''
A DatasetFile object is constructed by Dataset
it holds a netcdf file which belongs to a cycle
and a field and has its attributes computed
'''

class DatasetFile:
    def __init__(
        self,
        file: "File",
        dataset_field: "Field",
        dataset_cycle: "Cycle",
        id: Optional[int] = None,
        netcdf_file: Optional[NetcdfFile] = None
    ):
        self.file = file
        self.dataset_field = dataset_field
        self.dataset_cycle = dataset_cycle
        self.id = id
        self.netcdf_file = netcdf_file

    @classmethod
    def from_file(
        cls, 
        file_obj: "File", 
        dataset_field: "Field", 
        dataset_cycle: "Cycle"
    ) -> "DatasetFile":
        structure = None
        if dataset_field.obs_space:
            structure = dataset_field.obs_space.netcdf_structure

        nc_file = NetcdfFile.from_file(file_obj, structure)

        return cls(
            file=file_obj,
            dataset_field=dataset_field,
            dataset_cycle=dataset_cycle,
            netcdf_file=nc_file
        )

    @classmethod
    def from_orm(
        cls, 
        session, # Pass-through parameter, no explicit SQLAlchemy import needed
        orm: DatasetFileORM, 
        dataset_field: "Field", 
        dataset_cycle: "Cycle"
    ) -> "DatasetFile":
        file_domain = File.from_orm(orm.file)
        structure = dataset_field.obs_space.netcdf_structure
        nc_file = NetcdfFile.from_orm(session, orm.file, structure)

        return cls(
            file=file_domain,
            dataset_field=dataset_field,
            dataset_cycle=dataset_cycle,
            id=orm.id,
            netcdf_file=nc_file
        )

    def __repr__(self) -> str:
        return (
            f"<DatasetFile(id={self.id}, "
            "\n"
            # f"obs_space={self.dataset_field.obs_space.name}, "
            f"{self.dataset_field}, "
            "\n"
            # f"obs_space={self.dataset_field.obs_space}, "
            # f"cycle={self.dataset_cycle.cycle_date} {self.dataset_cycle.cycle_hour}, "
            f"{self.dataset_cycle}, "
            "\n"
            f"file={self.file.path})>"
        )

    def get_variable(self, path: str):
        return self.netcdf_file.get_variable(path)

    def to_orm(self) -> "DatasetFileORM":
        return DatasetFileORM(
            id=self.id,
            dataset_field_id=self.dataset_field.id,
            dataset_cycle_id=self.dataset_cycle.id,
            file_id=self.file.id
        )

    def get_surface_variable_data(self, variable_path):
        nc_file = self.netcdf_file
        variable_name = Path(variable_path).name

        return {
            "variable_name": variable_name,
            "dataset_name": self.dataset_field.dataset.name,
            "obs_space_name": self.dataset_field.obs_space.name,
            "values": nc_file.get_variable(f"{variable_path}"),
            "lons": nc_file.get_variable("/MetaData/longitude"),
            "lats": nc_file.get_variable("/MetaData/latitude"),
            "units": nc_file.get_node_attribute(variable_path, "units")
        }

    def has_derived(self, path: str, name: str):
        return self.netcdf_file.has_derived(path, name)
