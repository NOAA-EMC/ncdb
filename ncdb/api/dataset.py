import logging
from datetime import datetime

from .obsspace import ObsSpace
from .field import Field

logger = logging.getLogger(__name__)


class Dataset:
    def __init__(self, core_ds, repo):
        self._ds = core_ds
        self._repo = repo

        self._repo.load_fields(self._ds)
        if not self._ds.fields:
            # logger.error(f"Failed loading fields for dataset '{self.name}'")
            logger.warning(f"No fields loaded for dataset '{self.name}'")

        # self._cycles = None   # instead of []

    def __repr__(self):
        return (
            f"<Dataset "
            f"id={self._ds.id} "
            f"name={self._ds.name} "
            f"root_dir={self._ds.root_dir}>"
        )

    @property
    def name(self):
        return self._ds.name

    @property
    def id(self):
        return self._ds.id

    @property
    def root_dir(self):
        return self._ds.root_dir

    # @property
    # def cycles(self):
        # if self._cycles is None:
            # self._repo.load_cycles(self._ds)
            # self._cycles = self._ds.cycles
        # return self._cycles

    '''
    @property
    def cycles(self):
        if self._cycles is None:
            self._repo.load_cycles(self._ds)
            self._cycles = sorted(
                [
                    datetime(
                        c.cycle_date.year,
                        c.cycle_date.month,
                        c.cycle_date.day,
                        int(c.cycle_hour),
                    )
                    for c in self._ds.cycles
                ]
            )
        return self._cycles
    '''


    @property
    def cycles(self):
        """
        Return available dataset cycles as sorted datetime objects.
        """

        #
        # lazy-load cycles from repository
        #
        if not self._ds.cycles:
            self._repo.load_cycles(self._ds)

        return sorted(
            [
                datetime(
                    c.cycle_date.year,
                    c.cycle_date.month,
                    c.cycle_date.day,
                    int(c.cycle_hour),
                )
                for c in self._ds.cycles
            ]
        )


    # def list_obsspaces(self) -> list[str]:
        # return [f.obs_space.name for f in self._ds.fields]
    def obsspaces(self) -> list[str]:
        return [f.obs_space for f in self._ds.fields]

    def obsspace(self, name: str) -> ObsSpace:
        field = self._ds.find_field_by_name(name)
        if not field:
            raise ValueError(f"ObsSpace '{name}' not found")

        return ObsSpace(field, self._repo)
