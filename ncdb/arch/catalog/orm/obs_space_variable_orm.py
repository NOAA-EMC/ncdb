from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
)

from .base import Base


class ObsSpaceVariableORM(Base):
    __tablename__ = "obs_space_variables"

    obs_space_id = Column(
        Integer,
        ForeignKey("obs_spaces.id"),
        primary_key=True,
    )

    variable_id = Column(
        Integer,
        ForeignKey("variables.id"),
        primary_key=True,
    )
