from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    UniqueConstraint,
)
from .base import Base


class ObsSpaceFieldORM(Base):
    __tablename__ = "obs_space_fields"

    obs_space_id = Column(
        Integer,
        ForeignKey("obs_spaces.id"),
        primary_key=True,
    )

    field_id = Column(
        Integer,
        ForeignKey("fields.id"),
        primary_key=True,
    )

    # Optional: this field represents data associated
    # with this scientific variable.
    variable_id = Column(
        Integer,
        ForeignKey("variables.id"),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "obs_space_id",
            "field_id",
            name="uq_obs_space_field",
        ),
    )
