import logging

from .field import Field
from .evaluators import BaseVariableEvaluator

logger = logging.getLogger(__name__)


class ObsSpace:
    """
    API wrapper over ds.Field.
    """

    def __init__(self, field, repo):
        self._field = field
        self._repo = repo

        # cache structure
        self._structure = field.obs_space.netcdf_structure

        self._repo.load_field_files(self._field)

    def __repr__(self):
        return f"<ObsSpace {self.name}>"

    @property
    def name(self):
        return self._field.obs_space.name

    def field(self, name: str) -> Field:
        """
        the API Field corresponds to variable in netcdf.
        Resolve a variable by name or path.

        Examples:
            "lon"
            "ObsValue/seaSurfaceTemperature"
        """
        structure = self._field.obs_space.netcdf_structure

        # --- full path ---
        if "/" in name:
            path = structure.check_variable_path(name)
            if path:
                evaluator = BaseVariableEvaluator(self._field, path, self._repo)
                return Field(evaluator)
            else:
                raise ValueError(f"Field '{name}' not found")

        # --- short name ---
        paths = structure.find_variable_paths_by_name(name)

        if not paths:
            raise ValueError(f"Field '{name}' not found")

        if len(paths) > 1:
            raise ValueError(f"Field '{name}' is ambiguous. Matches: {paths}")

        evaluator = BaseVariableEvaluator(self._field, paths[0], self._repo)
        return Field(evaluator)

    def list_variables(self, group: str | None = None):
        structure = self._field.obs_space.netcdf_structure

        if group is None:
            return structure.list_variables()

        # normalize group → path
        if not group.startswith("/"):
            group = f"/{group}"

        return structure.list_variables(parent_path=group)
