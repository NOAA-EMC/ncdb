from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from .base import Base


class ObsSpaceORM(Base):
    """
    Global ObsSpace type definition.
    """

    __tablename__ = "obs_spaces"

    id = Column(Integer, primary_key=True)

    name = Column(
        String,
        unique=True,
        nullable=False,
    )

    netcdf_structure_id = Column(
        Integer,
        ForeignKey("netcdf_structures.id"),
        nullable=True,
    )

    netcdf_structure = relationship(
        "NetcdfStructureORM",
        back_populates="obs_spaces",
    )

    obs_space_variables = relationship(
        "ObsSpaceVariableORM",
        back_populates="obs_space",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<ObsSpaceORM("
            f"id={self.id}, "
            f"name='{self.name}')>"
        )
