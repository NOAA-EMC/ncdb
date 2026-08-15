from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    # UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .base import Base
from .obs_space_orm import ObsSpaceORM


class VariableORM(Base):
    """
    Logical scientific variable.

    A Variable represents an abstract physical quantity and is
    independent of any particular ObsSpace or physical storage.
    """

    __tablename__ = "variables"

    id = Column(Integer, primary_key=True)

    name = Column(
        String,
        nullable=False,
        unique=True,
    )

    description = Column(
        String,
        nullable=True,
    )

    obs_space_variables = relationship(
        "ObsSpaceVariableORM",
        back_populates="variable",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"<VariableORM("
            f"id={self.id}, "
            f"name='{self.name}')>"
        )


class ObsSpaceVariableORM(Base):
    """
    Associates an ObsSpace with a logical Variable.
    """

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

    obs_space = relationship(
        "ObsSpaceORM",
        back_populates="obs_space_variables",
    )

    variable = relationship(
        "VariableORM",
        back_populates="obs_space_variables",
    )
